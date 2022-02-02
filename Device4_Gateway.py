# 4つのデバイスと外部ルータをつなぐゲートウェイ
import switch_hub

from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import ether_types as types

# アドミッション制御に用いる変数を定義
INIT_TIME    = 10
POLLING_TIME = 30
REPLY_TIME   = 3

QOS_FLAG      = 'flag'
QOS_OFF       = 0
QOS_ON        = 1
QOS_IDLE_TIME = 0
QOS_PRIORITY  = 65535

TRAFFIC = 'traffic'
PRIORITY_1_TRAFFIC = 100
PRIORITY_2_TRAFFIC = 300
PRIORITY_3_TRAFFIC = 200
PRIORITY_4_TRAFFIC = 100

TOS            = 'tos'
PRIORITY_1_TOS = 32
PRIORITY_2_TOS = 16
PRIORITY_3_TOS = 8
PRIORITY_4_TOS = 4

ROUTER_MAC = '00:00:00:00:00:01'
PORT1_MAC = '00:00:00:00:00:02'
PORT2_MAC = '00:00:00:00:00:03'
PORT3_MAC = '00:00:00:00:00:04'
PORT4_MAC = '00:00:00:00:00:05'

ROUTER_PORT = 1
PRIORITY_1_PORT = 2
PRIORITY_2_PORT = 3
PRIORITY_3_PORT = 4
PRIORITY_4_PORT = 5

GATEWAY_PORT4 = '10.0.0.5'

PRIORITY_1_DC = 1
PRIORITY_2_DC = 1
PRIORITY_3_DC = 1
PRIORITY_4_DC = 1

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

        # 各優先度フローのドロップされた回数を保存
        self.dc = {PRIORITY_1_PORT:PRIORITY_1_DC,
                   PRIORITY_2_PORT:PRIORITY_2_DC,
                   PRIORITY_3_PORT:PRIORITY_3_DC,
                   PRIORITY_4_PORT:PRIORITY_4_DC}

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
            self.addmission_control()
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
    #def qos_setting(self):
    #    for port in self.traffic.keys():
    #        if self.traffic[port] - self.qos[port][TRAFFIC] > self.base[port]:
    #            if self.qos[port][QOS_FLAG] == QOS_OFF:
    #                self.add_qos(port)

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

    # フロー削除
    def del_qos(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        match = parser.OFPMatch(in_port=port, dl_type=types.ETH_TYPE_IP, dl_dst=haddr_to_bin(ROUTER_MAC))

        mod = parser.OFPFlowMod(datapath=self.datapath,
                                match=match, cookie=0,
                                command=ofproto.OFPFC_DELETE,
                                idle_timeout=QOS_IDLE_TIME,
                                priority=QOS_PRIORITY)

        self.datapath.send_msg(mod)

    # FlowRemovedイベントハンドラの作成
    # FLowRemovedイベントが発生したらQoS設定フラグをOFFに更新する
    # idle_timeoutによるフロー削除なら、対象ポートの統計情報を取得し通信量を更新する
    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def _flow_removed_handler(self, ev):
        msg = ev.msg
        port = msg.match.in_port
        self.qos[port][QOS_FLAG] = QOS_OFF
        self.dc[port] += 1
        if msg.reason == self.datapath.ofproto.OFPRR_IDLE_TIMEOUT:
            self.stats_request(self.datapath, port)
            hub.sleep(REPLY_TIME)
            self.qos[port][TRAFFIC] = self.traffic[port]
    
    # 各ポートの通信量更新を更新する
    def renew_traffic(self):
        for port in self.traffic.keys():
            self.qos[port][TRAFFIC] = self.traffic[port]

    # フローをドロップ
    # フローの処理内容を空白にする
    def drop_flow(self, port):
        ofproto = self.datapath.ofproto
        parser = self.datapath.ofproto_parser

        match = parser.OFPMatch(in_port=port, dl_type=types.ETH_TYPE_IP, dl_dst=haddr_to_bin(ROUTER_MAC))
        actions = []

        mod = parser.OFPFlowMod(datapath=self.datapath, match=match, cookie=0, command=ofproto.OFPFC_MODIFY, actions=actions)

        self.datapath.send_msg(mod)

    # アドミッション制御
    def addmission_control(self):
        #ofproto = self.datapath.ofproto
        #parser = self.datapath.ofproto_parser

        #actions = [parser.OFPActionOutput(ROUTER_PORT)]

        #a = 1

        switchhub = switch_hub.SwitchHub()

        switchhub.drop_flow(self.datapath, haddr_to_bin(PORT4_MAC))
        switchhub.del_dropped_flow(self.datapath)

        #if a > 0:
        #    switchhub.drop_flow(self.datapath, haddr_to_bin(PORT4_MAC))
        #    a += 1
        
        #switchhub.modify_flow(self.datapath, haddr_to_bin(PORT4_MAC), ROUTER_PORT)
        #switchhub.add_flow(self.datapath, PRIORITY_4_PORT, haddr_to_bin(PORT4_MAC), haddr_to_bin(ROUTER_PORT), actions)
        #switchhub.del_flow(self.datapath, haddr_to_bin(PORT4_MAC))

        #if a > 5:
        #    switchhub.del_dropped_flow(self.datapath)
        #    a = a - 5

        w2 = self.dc[PRIORITY_2_PORT] * (6 - PRIORITY_2_PORT)

        w3 = self.dc[PRIORITY_3_PORT] * (6 - PRIORITY_3_PORT)

        w4 = self.dc[PRIORITY_4_PORT] * (6 - PRIORITY_4_PORT)

        # 消したフローを再登録
        for port in self.traffic.keys():
            if self.traffic[port] - self.qos[port][TRAFFIC] > self.base[port]:
                if self.qos[port][QOS_FLAG] == QOS_OFF:
                    self.add_qos(port)

        # 1が通信帯域ないと
        if self.traffic[PRIORITY_1_PORT] - self.qos[PRIORITY_1_PORT][TRAFFIC] < self.base[PRIORITY_1_PORT]:

            # 2~4をドロップ
            # dcを用いてドロップするフローを選択
            if min([w2, w3, w4]) == w2:
                if self.qos[PRIORITY_2_PORT][QOS_FLAG] == QOS_ON:
                    self.drop_flow(PRIORITY_2_PORT)
                    self.del_qos(PRIORITY_2_PORT)
            elif min([w2, w3, w4]) == w3:
                if self.qos[PRIORITY_3_PORT][QOS_FLAG] == QOS_ON:
                    self.drop_flow(PRIORITY_3_PORT)
                    self.del_qos(PRIORITY_3_PORT)
            elif min([w2, w3, w4]) == w4:
                if self.qos[PRIORITY_4_PORT][QOS_FLAG] == QOS_ON:
                    #switchhub.drop_flow(self.datapath, haddr_to_bin(PORT4_MAC))
                    #switchhub.del_flow(self.datapath, haddr_to_bin(PORT4_MAC))
                    self.drop_flow(PRIORITY_3_PORT)
                    self.del_qos(PRIORITY_4_PORT)

            # 2が通信帯域ないと
            if self.traffic[PRIORITY_2_PORT] - self.qos[PRIORITY_2_PORT][TRAFFIC] < self.base[PRIORITY_2_PORT]:

                # 3~4をドロップ
                # dcを用いてドロップするフローを選択
                if min([w3, w4]) == w3:
                    if self.qos[PRIORITY_3_PORT][QOS_FLAG] == QOS_ON:
                        self.drop_flow(PRIORITY_3_PORT)
                        self.del_qos(PRIORITY_3_PORT)
                if min([w3, w4]) == w4:
                    if self.qos[PRIORITY_4_PORT][QOS_FLAG] == QOS_ON:
                        self.drop_flow(PRIORITY_4_PORT)
                        self.del_qos(PRIORITY_4_PORT)
