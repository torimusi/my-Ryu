from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

MAC_IDLE_TIME = 300


class SwitchHub(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SwitchHub, self).__init__(*args, **kwargs)
        self.mac_to_port = {}

    def add_flow(self, datapath, in_port, src, dst, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(in_port=in_port, dl_src=src, dl_dst=dst)

        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0, idle_timeout=MAC_IDLE_TIME, command=ofproto.OFPFC_ADD,actions=actions)

        datapath.send_msg(mod)

    def del_flow(self, datapath, mac):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(dl_src=mac)

        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0,
        command=ofproto.OFPFC_DELETE)

        datapath.send_msg(mod)

    def modify_flow(self, datapath, mac, port):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(dl_dst=mac)

        actions = [datapath.ofproto_parser.OFPActionOutput(port)]

        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0, idle_timeout=MAC_IDLE_TIME, command=ofproto.OFPFC_MODIFY,actions=actions)

        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.mac_to_port[dpid].setdefault(src, msg.in_port)

        if self.mac_to_port[dpid][src] != msg.in_port:
            self.del_flow(datapath, haddr_to_bin(src))
            self.modify_flow((datapath, haddr_to_bin(src), msg.in_port)
            self.mac_to_port[dpid][src] = msg.in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            self.add_flow(datapath, msg.in_port, haddr_to_bin(src), haddr_to_bin(dst), actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id, in_port=msg.in_port, actions=actions, data=data)
        datapath.send_msg(out)