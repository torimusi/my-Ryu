from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_0
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib import hub
from ryu.lib.packet import ether_types as types

MAC_IDLE_TIME = 300

# アドミッション制御に用いる変数を定義
INIT_TIME    = 10
POLLING_TIME = 60
REPLY_TIME   = 3

QOS_FLAG      = 'flag'
QOS_OFF       = 0
QOS_ON        = 1
QOS_IDLE_TIME = 0
QOS_PRIORITY  = 65535

TRAFFIC = 'traffic'
PRIORITY_1_TRAFFIC = 100 * (10 ** 1)
PRIORITY_2_TRAFFIC = 300 * (10 ** 1)
PRIORITY_3_TRAFFIC = 200 * (10 ** 1)
PRIORITY_4_TRAFFIC = 100 * (10 ** 1)

TOS            = 'tos'
PRIORITY_1_TOS = 32
PRIORITY_2_TOS = 16
PRIORITY_3_TOS = 8
PRIORITY_4_TOS = 4

ROUTER_MAC = '00:00:00:00:00:01'
ROUTER_PORT = 1

PRIORITY_1_PORT = 2
PRIORITY_2_PORT = 3
PRIORITY_3_PORT = 4
PRIORITY_4_PORT = 5

PRIORITY_1_DC = 1
PRIORITY_2_DC = 1
PRIORITY_3_DC = 1
PRIORITY_4_DC = 1


class SwitchHub(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_0.OFP_VERSION]

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
            self.modify_flow(datapath, haddr_to_bin(src), msg.in_port)
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