# 4つのデバイスと外部ルータをつなぐゲートウェイ
from ryu.app import switch_hub

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import ether_types as types

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
class Device4Gateway(switch_hub.SwitchHub):

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

        # モニタスレッド
        self.monitor_thread = hub.spawn(self._qos_monitor)

    @set_ev_cls(ofp_event.EventOFPStateChange, MAIN_DISPATCHER)
    def _state_change_handler(self, ev):
        self.datapath = ev.datapath

    # モニタスレッド
    # ポートの統計情報を取得・辞書に通信量保存
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

    def stats_request(self, datapath, port):
        req = datapath.ofproto_parser.OFPPortStatsRequest(datapath, 0, port)
        datapath.send_msg(req)

    # PortStatsReplyイベントハンドラの作成
    # PortStatsReplyメッセージを受信したら各ポートの通信量を更新
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        for stat in body:
            if stat.port_no in self.traffic.keys():
                self.traffic[stat.port_no] = stat.rx_bytes + stat.tx_bytes

    # QoS設定
    # 各ポートの通信量が既定値を超えた場合、ToSフィールドを書き換える
    def qos_setting(self):
        for port in self.traffic.keys():
            if self.tarffic[port] - self.qos[port][TRAFFIC] > self.base[port]:
                if self.qos[port][QOS_FLAG] == QOS_OFF:
                    self.add_qos(port)

    # フロー登録
    # フローを登録し、QoS設定フラグをONに更新する
    def add_qos(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        match = parser.OFPMatch(in_port=port, dl_type=types.ETH_TYPE_IP,
        dl_dst=haddr_to_bin(ROUTER_MAC))

        actions = [parser.OFPActionSetNwTos(self.qos[port][TOS]), parser.OFPActionOutput(ROUTER_PORT)]

        mod = parser.OFPFlowMod(datapath=self.datapath, 
                                match=match, cookie=0, 
                                command=ofproto.OFPFC_ADD, 
                                idle_timeout=QOS_IDLE_TIME,
                                priority=QOS_PRIORITY, 
                                flags=ofproto.OFPFF_SEND_FLOW_REM, 
                                actions=actions)

        self.datapath.send_msg(mod)

        self.qos[port][QOS_FLAG] = QOS_ON




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


    
    