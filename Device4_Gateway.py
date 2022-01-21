# 4つのデバイスと外部ルータをつなぐゲートウェイ

from distutils import command
from termios import TOSTOP
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet

# アドミッション制御に用いる変数を定義
INIT_TIME    = 10
POLLING_TIME = 300
REPLY_TIME   = 3

QOS_FLAG      = 'flag'
QOS_OFF       = 0
QOS_ON        = 1
QOS_IDLE_TIME = 120
QOS_PRIORITY  = 65535

TRAFFIC = 'traffic'
PRIORITY_1_TRAFFIC = 100 * (10 ** 6)
PRIORITY_2_TRAFFIC = 300 * (10 ** 6)
PRIORITY_3_TRAFFIC = 300 * (10 ** 6)
PRIORITY_4_TRAFFIC = 100 * (10 ** 6)

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

        self.add_flow(datapath, port)

    # フロー登録
    # 各ポートに各優先度のデバイスが接続
    # 送信先は外部ルータ
    def add_flow(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        # ポートを見てフロー登録、送信先はルータ
        match = parser.OFPMatch(in_port=port, dl_type=types.ETH_TYPE_IP, dl_dst=haddr_to_bin(ROUTER_MAC))
        actions = [parser.OFPActionSetNWTos(self.qos[port][TOS]), parser.OFPActionOutput(ROUTER_PORT)]

        mod = parser.OFPFlowMod(datapath=self.datapath, match=match, command=ofproto.OFPFC_ADD, actions=actions)

        self.datapath.send_msg(mod)

        self.qos[port][QOS_FLAG] = QOS_ON

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

    # モニタスレッド、ポートの統計情報を取得・辞書に通信量保存
    def _qos_monitor(self):
        # 設定初期化
        while True:
            if self.datapath:
                self.stats_request(self.datapath, self.datapath.ofproto.OFPP_NONE)
                self.renew_traffic()
                break
            hub.sleep(INIT_TIME)

        hub.sleep(POLLING_TIME)
        while True:
            self.stats_request(self.datapath, self.datapath.ofproto.OFPP_NONE)
            hub.sleep(REPLY_TIME)
            self.qos_setting()
            self.renew_traffic()
            hub.sleep(POLLING_TIME)

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


    
    