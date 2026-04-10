from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ether_types, arp

class ArpProxyApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ArpProxyApp, self).__init__(*args, **kwargs)
        self.arp_table = {}
        # Rubric Requirement: Show allowed vs blocked scenarios
        self.blocked_ip = "10.0.0.3" 

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        
        eth_header = pkt.get_protocols(ethernet.ethernet)[0]
        arp_header = pkt.get_protocol(arp.arp)

        if eth_header.ethertype == ether_types.ETH_TYPE_ARP and arp_header:
            self.handle_arp(datapath, in_port, eth_header, arp_header)
            return

        self.forward_packet(msg, datapath, in_port, eth_header)

    def handle_arp(self, datapath, in_port, eth_header, arp_header):
        src_ip = arp_header.src_ip
        src_mac = arp_header.src_mac
        dst_ip = arp_header.dst_ip

        if src_ip not in self.arp_table:
            self.arp_table[src_ip] = src_mac
            self.logger.info(f"[LEARNED] {src_ip} is at {src_mac}")

        if dst_ip == self.blocked_ip:
            self.logger.info(f"[BLOCKED] Dropping ARP request for blocked IP: {dst_ip}")
            return

        if arp_header.opcode == arp.ARP_REQUEST:
            if dst_ip in self.arp_table:
                self.logger.info(f"[INTERCEPT] Generating ARP Reply for {dst_ip}")
                self.send_arp_reply(datapath, src_mac, src_ip, self.arp_table[dst_ip], dst_ip, in_port)
            else:
                self.logger.info(f"[MISS] Don't know {dst_ip}. Flooding ARP Request.")
                self.flood_packet(datapath, in_port, eth_header, arp_header)

    def send_arp_reply(self, datapath, dst_mac, dst_ip, src_mac, src_ip, out_port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        e = ethernet.ethernet(dst=dst_mac, src=src_mac, ethertype=ether_types.ETH_TYPE_ARP)
        a = arp.arp(hwtype=1, proto=0x0800, hlen=6, plen=4, opcode=arp.ARP_REPLY,
                    src_mac=src_mac, src_ip=src_ip, dst_mac=dst_mac, dst_ip=dst_ip)
        p = packet.Packet()
        p.add_protocol(e)
        p.add_protocol(a)
        p.serialize()
        actions = [parser.OFPActionOutput(out_port)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=ofproto.OFPP_CONTROLLER, actions=actions, data=p.data)
        datapath.send_msg(out)

    def flood_packet(self, datapath, in_port, eth_header, arp_header):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=ofproto.OFP_NO_BUFFER,
                                  in_port=in_port, actions=actions, data=None)
        datapath.send_msg(out)

    def forward_packet(self, msg, datapath, in_port, eth_header):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=msg.data)
        datapath.send_msg(out)
