from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

# クラスの定義
class gateway(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # 初期化
    def __init__(self, *args, **kwargs):
        super(gateway, self).__init__(*args, **kwargs)

    # Packet_Inイベントハンドラの作成
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.add_flow(datapath, priority, match, actions)

    # フロー登録
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # 優先度1
        match = parser.OFPMatch(in_port=HOST1_PORT)
        actions = [parser.OFPActionOutput(HOST2_PORT)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)

        datapath.send_msg(mod)

        # 優先度2
        match = parser.OFPMatch(in_port=HOST1_PORT)
        actions = [parser.OFPActionOutput(HOST2_PORT)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)

        datapath.send_msg(mod)

        # 優先度3
        match = parser.OFPMatch(in_port=HOST1_PORT)
        actions = [parser.OFPActionOutput(HOST2_PORT)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)

        datapath.send_msg(mod)

        # 優先度4
        match = parser.OFPMatch(in_port=HOST1_PORT)
        actions = [parser.OFPActionOutput(HOST2_PORT)]

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

        mod = parser.OFPFlowMod(datapath=datapath, priority=priority, match=match, instructions=inst)

        datapath.send_msg(mod)

    # フロー削除
    @set_ev_cls()
    def del_flow(self, datapath, mac):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(dl_src=mac)

        mod = parser.OFPFlowMod(datapath=datapath, match=match, cookie=0, command=ofproto.OFPFC_DELETE)

        datapath.send_msg(mod)

    # アドミッション制御
    def addmission_control():


        # Cat1のQoSが満たされていない時
        if 帯域 < 閾値
            # ドロップするフローを探す
            # フローをドロップ
            del_flow()
            # dc + 1
            フロー.dc + 1
            # Cat1のQoSを確認

    
    