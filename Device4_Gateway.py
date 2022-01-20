# 4つのデバイスと外部ルータをつなぐゲートウェイ

from distutils import command
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

# クラスの定義
class Device4Gateway(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    # 初期化
    def __init__(self, *args, **kwargs):
        super(Device4Gateway, self).__init__(*args, **kwargs)

        self.datapath = {}

        # 各ポートのアドミッション制御の基準となる通信量を規定
        self.base = {PRIORITY_1_PORT:PRIORITY_1_TRAFFIC,
                     PRIORITY_2_PORT:PRIORITY_2_TRAFFIC,
                     PRIORITY_3_PORT:PRIORITY_3_TRAFFIC,
                     PRIORITY_4_PORT:PRIORITY_4_TRAFFIC}

        # 各ポートの通信量を保存
        self.traffic = {PRIORITY_1_PORT:0,
                        PRIORITY_2_PORT:0,
                        PRIORITY_3_PORT:0,
                        PRIORITY_4_PORT:0,}

        # 前回取得した通信量、QoS設定フラグ、ToSフィールドの設定値を保存
        self.qos = {PRIORITY_1_PORT:{TRAFFIC:0, QOS_FLAG:QOS_OFF, TOS:PRIORITY_1_TOS},
                    PRIORITY_2_PORT:{TRAFFIC:0, QOS_FLAG:QOS_OFF, TOS:PRIORITY_2_TOS},
                    PRIORITY_3_PORT:{TRAFFIC:0, QOS_FLAG:QOS_OFF, TOS:PRIORITY_3_TOS},
                    PRIORITY_4_PORT:{TRAFFIC:0, QOS_FLAG:QOS_OFF, TOS:PRIORITY_4_TOS}}

    # Packet_Inイベントハンドラの作成
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.add_flow(datapath, priority, match, actions)

    # フロー登録
    # 各ポートに各優先度のデバイスが接続
    # 送信先は外部ルータ
    def add_flow(self, datapath, in_port, src, dst, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # ポートを見てフロー登録、送信先はルータ
        match = parser.OFPMatch(in_port=in_port, dl_src=src, dl_dst=dst)
        actions = [parser.OFPActionOutput(Router)]

        mod = parser.OFPFlowMod(datapath=datapath, match=match, command=ofproto.OFPFC_ADD, actions=actions)

        datapath.send_msg(mod)

    # フローをドロップ
    def drop_flow(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = []

        mod = parser.OFPFlowMod(datapath=self.datapath, match=match, cookie=0, command=ofproto.OFPFC_MODIFY, actions=actions)

        self.datapath.send_msg(mod)

    # フローを削除
    def del_flow(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        match = parser.OFPMatch()

        mod = parser.OFPFlowMod(datapath=self.datapath, match=match, cookie=0, command=ofproto.OFPFC_DELETE)

        self.datapath.send_msg(mod)

    # アドミッション制御
    def addmission_control():

        # Cat1のQoSが満たされていない時
        if 帯域 < 閾値
            # ドロップするフローを探す

            # フローをドロップ
            drop_flow()
            dc + 1

            # 優先度1のQoSが満たされたら

            # ドロップ確認後、フローを削除
            del_flow()


    
    