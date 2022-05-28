import configparser
import datetime
import json
import os
from typing import List, Optional

import boto3
import requests

TMP_DIR = "./tmp"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"


class EventSetting:
    setting_name: str
    ranking_json_url: str
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_region: str
    s3_bucket: str
    s3_folder: str
    save_file_prefix: str

    def __init__(self, setting_name: str, ranking_json_url: str, aws_access_key_id: str, aws_secret_access_key: str,
                 aws_region: str, s3_bucket: str, s3_folder: str, save_file_prefix: str):
        self.setting_name = setting_name
        self.ranking_json_url = ranking_json_url
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        self.s3_bucket = s3_bucket
        self.s3_folder = s3_folder
        self.save_file_prefix = save_file_prefix


class NicoGiftEventLoader:
    def __init__(self):
        self.event_settings = self.read_event_settings()

    def start(self):
        for event_setting in self.event_settings:
            date = datetime.datetime.now()
            timestamp = int(date.timestamp())
            print(f"*** {date}")
            print(f"{event_setting.ranking_json_url}")

            # 1. Get Ranking Data
            text = NicoGiftEventLoader.get_ranking_json(event_setting.ranking_json_url)
            print(text)
            if text is None:
                continue

            # 2. Save Data Locally
            filename = f"{event_setting.save_file_prefix}_{date.strftime('%Y%m%d%H%M%S')}_{timestamp}.json"
            NicoGiftEventLoader.save_ranking_json(
                text,
                TMP_DIR,
                filename
            )

            # 3. Configure AWS Session
            NicoGiftEventLoader.set_aws_environmental_values(
                event_setting.aws_access_key_id,
                event_setting.aws_secret_access_key,
                event_setting.aws_region,
            )

            # 4. Backup Data to S3
            NicoGiftEventLoader.backup_json_to_s3(
                TMP_DIR,
                filename,
                event_setting.s3_bucket,
                event_setting.s3_folder,
            )

            # 5. Insert Data to DynamoDB
            sample = '{"meta":{"status":200},"data":{"entry_items":[{"id":9416,"item_type":"user","item_id":"54091817","status":"enable","total_score":61080,"name":"うせつ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5409/54091817.jpg?1653667157","related_items":null,"rank":1},{"id":7902,"item_type":"user","item_id":"61407180","status":"enable","total_score":39340,"name":"とろみ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/6140/61407180.jpg?1516790391","related_items":null,"rank":2},{"id":9357,"item_type":"user","item_id":"56428427","status":"enable","total_score":34930,"name":"豚王a.k.a角煮","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5642/56428427.jpg?1652889579","related_items":null,"rank":3},{"id":9313,"item_type":"user","item_id":"94106156","status":"enable","total_score":29350,"name":"シンカモン","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9410/94106156.jpg?1626014562","related_items":null,"rank":4},{"id":9443,"item_type":"user","item_id":"97191053","status":"enable","total_score":21570,"name":"イノシシ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9719/97191053.jpg?1619450611","related_items":null,"rank":5},{"id":7678,"item_type":"user","item_id":"21307368","status":"enable","total_score":20860,"name":"旅猫あずき","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2130/21307368.jpg?1610796531","related_items":null,"rank":6},{"id":8901,"item_type":"user","item_id":"87615466","status":"enable","total_score":16540,"name":"古知屋","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8761/87615466.jpg?1646644790","related_items":null,"rank":7},{"id":7529,"item_type":"user","item_id":"19334237","status":"enable","total_score":16460,"name":"フグちゃん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1933/19334237.jpg?1645421594","related_items":null,"rank":8},{"id":9512,"item_type":"user","item_id":"334810","status":"enable","total_score":13570,"name":"AIR.","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/33/334810.jpg?1479893478","related_items":null,"rank":9},{"id":7990,"item_type":"user","item_id":"63355594","status":"enable","total_score":13080,"name":"牛脂ちゃん［20］","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/6335/63355594.jpg?1625080283","related_items":null,"rank":10},{"id":7659,"item_type":"user","item_id":"58852571","status":"enable","total_score":11580,"name":"あおこ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5885/58852571.jpg?1606328609","related_items":null,"rank":11},{"id":9387,"item_type":"user","item_id":"116144654","status":"enable","total_score":11520,"name":"大仏","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11614/116144654.jpg?1644884048","related_items":null,"rank":12},{"id":7534,"item_type":"user","item_id":"96901476","status":"enable","total_score":9390,"name":"コスガーゼロ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9690/96901476.jpg?1630780333","related_items":null,"rank":13},{"id":9347,"item_type":"user","item_id":"11908507","status":"enable","total_score":8760,"name":"向日葵(ひまわり)2nd","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1190/11908507.jpg?1559254010","related_items":null,"rank":14},{"id":7911,"item_type":"user","item_id":"52489331","status":"enable","total_score":8610,"name":"伊藤福島","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5248/52489331.jpg?1609427444","related_items":null,"rank":15},{"id":7909,"item_type":"user","item_id":"117650811","status":"enable","total_score":8160,"name":"たこすちゃん（本垢）","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11765/117650811.jpg?1634008524","related_items":null,"rank":16},{"id":9082,"item_type":"user","item_id":"3318785","status":"enable","total_score":7680,"name":"伊勢エビ子","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/331/3318785.jpg?1618951691","related_items":null,"rank":17},{"id":8128,"item_type":"user","item_id":"5599432","status":"enable","total_score":6510,"name":"おったん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/559/5599432.jpg?1505573544","related_items":null,"rank":18},{"id":7817,"item_type":"user","item_id":"32776155","status":"enable","total_score":5830,"name":"法金蔵","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3277/32776155.jpg?1470074476","related_items":null,"rank":19},{"id":7980,"item_type":"user","item_id":"73051178","status":"enable","total_score":4230,"name":"MIKO","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/7305/73051178.jpg?1649807947","related_items":null,"rank":20},{"id":8631,"item_type":"user","item_id":"123127546","status":"enable","total_score":3120,"name":"かさぴ〜","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12312/123127546.jpg?1647414042","related_items":null,"rank":21},{"id":9172,"item_type":"user","item_id":"197684","status":"enable","total_score":3100,"name":"みずかがみ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/19/197684.jpg?1442650987","related_items":null,"rank":22},{"id":7950,"item_type":"user","item_id":"118387021","status":"enable","total_score":2890,"name":"甘辛ゆんゆん　　　　　　　　。。","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11838/118387021.jpg?1646773746","related_items":null,"rank":23},{"id":8443,"item_type":"user","item_id":"114849","status":"enable","total_score":2700,"name":"pote","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11/114849.jpg?1589816757","related_items":null,"rank":24},{"id":9361,"item_type":"user","item_id":"88967456","status":"enable","total_score":2690,"name":"やまおか","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8896/88967456.jpg?1652446263","related_items":null,"rank":25},{"id":9317,"item_type":"user","item_id":"98275441","status":"enable","total_score":2570,"name":"ぇりぃ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9827/98275441.jpg?1600411685","related_items":null,"rank":26},{"id":9086,"item_type":"user","item_id":"52553742","status":"enable","total_score":2510,"name":"贅肉ちゃん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5255/52553742.jpg?1612617546","related_items":null,"rank":27},{"id":7890,"item_type":"user","item_id":"7965239","status":"enable","total_score":2140,"name":"蒼夜の狙撃手","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":28},{"id":9058,"item_type":"user","item_id":"95960370","status":"enable","total_score":1940,"name":"山口ムスメ→月城様","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9596/95960370.jpg?1653181291","related_items":null,"rank":29},{"id":8877,"item_type":"user","item_id":"121193886","status":"enable","total_score":1870,"name":"しろまる枠❤️⭐️✨(´△｀*)","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12119/121193886.jpg?1644149101","related_items":null,"rank":30},{"id":7609,"item_type":"user","item_id":"36591468","status":"enable","total_score":1760,"name":"D.Y(男爵山下)","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3659/36591468.jpg?1651479370","related_items":null,"rank":31},{"id":9115,"item_type":"user","item_id":"120089756","status":"enable","total_score":1700,"name":"レトロめゲーマー　コウ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12008/120089756.jpg?1626619909","related_items":null,"rank":32},{"id":8719,"item_type":"user","item_id":"51610839","status":"enable","total_score":1660,"name":"ようずん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5161/51610839.jpg?1621191657","related_items":null,"rank":33},{"id":8651,"item_type":"user","item_id":"123305173","status":"enable","total_score":1610,"name":"Haru","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12330/123305173.jpg?1652400639","related_items":null,"rank":34},{"id":8022,"item_type":"user","item_id":"116097394","status":"enable","total_score":1600,"name":"磯野くん...","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11609/116097394.jpg?1647766235","related_items":null,"rank":35},{"id":7718,"item_type":"user","item_id":"61674574","status":"enable","total_score":1600,"name":"ゆうちゃん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/6167/61674574.jpg?1584093054","related_items":null,"rank":36},{"id":9358,"item_type":"user","item_id":"19260549","status":"enable","total_score":1500,"name":"リサリサどっとこむ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1926/19260549.jpg?1498194947","related_items":null,"rank":37},{"id":8992,"item_type":"user","item_id":"18231793","status":"enable","total_score":1470,"name":"ちんちくりん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1823/18231793.jpg?1653382534","related_items":null,"rank":38},{"id":8190,"item_type":"user","item_id":"116490822","status":"enable","total_score":1440,"name":"くろぬこ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11649/116490822.jpg?1605370474","related_items":null,"rank":39},{"id":7626,"item_type":"user","item_id":"86779446","status":"enable","total_score":1420,"name":"まろやか。  ˖ ☆","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8677/86779446.jpg?1581116541","related_items":null,"rank":40},{"id":9154,"item_type":"user","item_id":"13828602","status":"enable","total_score":1320,"name":"落合健一","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1382/13828602.jpg?1641282256","related_items":null,"rank":41},{"id":7771,"item_type":"user","item_id":"7892757","status":"enable","total_score":1080,"name":"地鏡(ジカガミ)","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/789/7892757.jpg?1631783602","related_items":null,"rank":42},{"id":8016,"item_type":"user","item_id":"20913510","status":"enable","total_score":1000,"name":"Piちゃんねる","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2091/20913510.jpg?1650636181","related_items":null,"rank":43},{"id":7566,"item_type":"user","item_id":"80285519","status":"enable","total_score":1000,"name":"安達悟","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8028/80285519.jpg?1653268499","related_items":null,"rank":44},{"id":8500,"item_type":"user","item_id":"15868877","status":"enable","total_score":870,"name":"柊﨑悶太郎（くきさき）","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1586/15868877.jpg?1629290727","related_items":null,"rank":45},{"id":8947,"item_type":"user","item_id":"51907","status":"enable","total_score":830,"name":"大神一郎(改)","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":46},{"id":8248,"item_type":"user","item_id":"35366553","status":"enable","total_score":740,"name":"眩暈","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3536/35366553.jpg?1561286740","related_items":null,"rank":47},{"id":8378,"item_type":"user","item_id":"116291138","status":"enable","total_score":700,"name":"釉妃夏-Yuina-","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11629/116291138.jpg?1653359701","related_items":null,"rank":48},{"id":8987,"item_type":"user","item_id":"34646763","status":"enable","total_score":670,"name":"ゼム","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3464/34646763.jpg?1651441609","related_items":null,"rank":49},{"id":9616,"item_type":"user","item_id":"29133122","status":"enable","total_score":660,"name":"酒カス","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2913/29133122.jpg?1485565435","related_items":null,"rank":50},{"id":9506,"item_type":"user","item_id":"38762035","status":"enable","total_score":660,"name":"勇者トロ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3876/38762035.jpg?1525100662","related_items":null,"rank":51},{"id":8811,"item_type":"user","item_id":"52096554","status":"enable","total_score":590,"name":"くろすて","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5209/52096554.jpg?1580215111","related_items":null,"rank":52},{"id":9285,"item_type":"user","item_id":"91204361","status":"enable","total_score":570,"name":"なんにも梨　　　　　　　　♡★♡","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/9120/91204361.jpg?1640179972","related_items":null,"rank":53},{"id":8198,"item_type":"user","item_id":"30338847","status":"enable","total_score":570,"name":"mini","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3033/30338847.jpg?1642705070","related_items":null,"rank":54},{"id":7811,"item_type":"user","item_id":"124366883","status":"enable","total_score":550,"name":"ノーア","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12436/124366883.jpg?1651991553","related_items":null,"rank":55},{"id":9465,"item_type":"user","item_id":"123476201","status":"enable","total_score":530,"name":"47歳無職まー","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":56},{"id":8387,"item_type":"user","item_id":"906189","status":"enable","total_score":520,"name":"ネシャーマ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/90/906189.jpg?1575970856","related_items":null,"rank":57},{"id":8763,"item_type":"user","item_id":"15502152","status":"enable","total_score":510,"name":"ウロ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1550/15502152.jpg?1630842587","related_items":null,"rank":58},{"id":7574,"item_type":"user","item_id":"23667325","status":"enable","total_score":470,"name":"りぃたん　　　　　　　　　　　。","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2366/23667325.jpg?1495019293","related_items":null,"rank":59},{"id":8405,"item_type":"user","item_id":"277711","status":"enable","total_score":460,"name":"ずぼら","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":60},{"id":7594,"item_type":"user","item_id":"65869799","status":"enable","total_score":430,"name":"だだだ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/6586/65869799.jpg?1652011045","related_items":null,"rank":61},{"id":9434,"item_type":"user","item_id":"4741686","status":"enable","total_score":390,"name":"岡山芸人　京極","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/474/4741686.jpg?1645836618","related_items":null,"rank":62},{"id":7604,"item_type":"user","item_id":"85402465","status":"enable","total_score":390,"name":"サーラちゃんさま小公国","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8540/85402465.jpg?1633273774","related_items":null,"rank":63},{"id":8552,"item_type":"user","item_id":"5369207","status":"enable","total_score":380,"name":"しい","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":64},{"id":8193,"item_type":"user","item_id":"59359575","status":"enable","total_score":350,"name":"ゆんゆん。。 　　　　　　　 .","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5935/59359575.jpg?1650185487","related_items":null,"rank":65},{"id":9530,"item_type":"user","item_id":"85367446","status":"enable","total_score":340,"name":"月光天照2022おめで寅☆彡","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8536/85367446.jpg?1642628261","related_items":null,"rank":66},{"id":7809,"item_type":"user","item_id":"122427907","status":"enable","total_score":340,"name":"あるないち","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12242/122427907.jpg?1641434042","related_items":null,"rank":67},{"id":8242,"item_type":"user","item_id":"16284711","status":"enable","total_score":330,"name":"国家非常事態宣言","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1628/16284711.jpg?1423381507","related_items":null,"rank":68},{"id":9379,"item_type":"user","item_id":"931735","status":"enable","total_score":310,"name":"ちーず・ばたー","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/93/931735.jpg?1629738372","related_items":null,"rank":69},{"id":9284,"item_type":"user","item_id":"56092654","status":"enable","total_score":310,"name":"黒田パン蔵","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5609/56092654.jpg?1617611199","related_items":null,"rank":70},{"id":7569,"item_type":"user","item_id":"74947723","status":"enable","total_score":310,"name":"おまたせっぽい","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/7494/74947723.jpg?1619865657","related_items":null,"rank":71},{"id":9489,"item_type":"user","item_id":"95636779","status":"enable","total_score":300,"name":"海砂利水魚　　　　　　　　　　。","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/defaults/blank.jpg","related_items":null,"rank":72},{"id":8745,"item_type":"user","item_id":"118350720","status":"enable","total_score":300,"name":"おふモグラ2022皐月MAY","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11835/118350720.jpg?1648789225","related_items":null,"rank":73},{"id":7802,"item_type":"user","item_id":"115986961","status":"enable","total_score":300,"name":"かぜの。iP","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/11598/115986961.jpg?1648183612","related_items":null,"rank":74},{"id":8943,"item_type":"user","item_id":"18396371","status":"enable","total_score":290,"name":"kawa","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1839/18396371.jpg?1626270590","related_items":null,"rank":75},{"id":8531,"item_type":"user","item_id":"77604904","status":"enable","total_score":290,"name":"ジェントルマン ヒデ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/7760/77604904.jpg?1517186949","related_items":null,"rank":76},{"id":8446,"item_type":"user","item_id":"120134738","status":"enable","total_score":290,"name":"ほいと","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12013/120134738.jpg?1626936743","related_items":null,"rank":77},{"id":7738,"item_type":"user","item_id":"121329803","status":"enable","total_score":290,"name":"上野でおなじみの俺","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12132/121329803.jpg?1633992933","related_items":null,"rank":78},{"id":9476,"item_type":"user","item_id":"124397125","status":"enable","total_score":270,"name":"豆腐","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12439/124397125.jpg?1653623091","related_items":null,"rank":79},{"id":8630,"item_type":"user","item_id":"51260160","status":"enable","total_score":270,"name":"へなちょこサダ＠ロングニート","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5126/51260160.jpg?1573464752","related_items":null,"rank":80},{"id":7711,"item_type":"user","item_id":"7556148","status":"enable","total_score":270,"name":"ニコラ津山","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/755/7556148.jpg?1632313934","related_items":null,"rank":81},{"id":9385,"item_type":"user","item_id":"21707288","status":"enable","total_score":230,"name":"わたがめ","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2170/21707288.jpg?1640330449","related_items":null,"rank":82},{"id":9205,"item_type":"user","item_id":"584765","status":"enable","total_score":230,"name":"マテリアル仲宗根","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/58/584765.jpg?1586646678","related_items":null,"rank":83},{"id":8607,"item_type":"user","item_id":"18663405","status":"enable","total_score":210,"name":"ゆうーーーーーーーーーーーー","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1866/18663405.jpg?1645317252","related_items":null,"rank":84},{"id":8187,"item_type":"user","item_id":"7422045","status":"enable","total_score":200,"name":"ごろー@ジェイドボックス＆怪談","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/742/7422045.jpg?1629703050","related_items":null,"rank":85},{"id":8026,"item_type":"user","item_id":"11379012","status":"enable","total_score":200,"name":"雑魚寝","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1137/11379012.jpg?1650697334","related_items":null,"rank":86},{"id":9382,"item_type":"user","item_id":"563949","status":"enable","total_score":190,"name":"あひる","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/56/563949.jpg?1623847014","related_items":null,"rank":87},{"id":7930,"item_type":"user","item_id":"56365080","status":"enable","total_score":180,"name":"大雪シャオロン","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/5636/56365080.jpg?1653083767","related_items":null,"rank":88},{"id":8336,"item_type":"user","item_id":"20096336","status":"enable","total_score":170,"name":"夢見空児（ゆめみくうじ）","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/2009/20096336.jpg?1571990713","related_items":null,"rank":89},{"id":7753,"item_type":"user","item_id":"14014777","status":"enable","total_score":170,"name":"リバさん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1401/14014777.jpg?1646231569","related_items":null,"rank":90},{"id":7537,"item_type":"user","item_id":"87149482","status":"enable","total_score":170,"name":"汁子","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/8714/87149482.jpg?1574682086","related_items":null,"rank":91},{"id":9350,"item_type":"user","item_id":"13630731","status":"enable","total_score":160,"name":"鹿男馬　漢（銀賞コレクター）阿斗","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/1363/13630731.jpg?1645711117","related_items":null,"rank":92},{"id":9016,"item_type":"user","item_id":"9594121","status":"enable","total_score":160,"name":"まりぐにゃん","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/959/9594121.jpg?1566369167","related_items":null,"rank":93},{"id":8759,"item_type":"user","item_id":"123026157","status":"enable","total_score":150,"name":"Em光晴","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/12302/123026157.jpg?1644897927","related_items":null,"rank":94},{"id":8506,"item_type":"user","item_id":"32912222","status":"enable","total_score":150,"name":"S＆P(ｴｽﾋﾟｰ)","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/3291/32912222.jpg?1642073418","related_items":null,"rank":95},{"id":8298,"item_type":"user","item_id":"8508182","status":"enable","total_score":150,"name":"レオン閣下","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/850/8508182.jpg?1259922544","related_items":null,"rank":96},{"id":7947,"item_type":"user","item_id":"4164483","status":"enable","total_score":150,"name":"青春ブタ野郎　　　　　　　　　．","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/416/4164483.jpg?1289662867","related_items":null,"rank":97},{"id":9543,"item_type":"user","item_id":"6137788","status":"enable","total_score":140,"name":"ニンポー","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/613/6137788.jpg?1645606758","related_items":null,"rank":98},{"id":9432,"item_type":"user","item_id":"42715621","status":"enable","total_score":140,"name":"かんむりの人生日記","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/4271/42715621.jpg?1628503834","related_items":null,"rank":99},{"id":8756,"item_type":"user","item_id":"6058667","status":"enable","total_score":140,"name":"みやた","thumbnail_url":"https://secure-dcdn.cdn.nimg.jp/nicoaccount/usericon/605/6058667.jpg?1650363427","related_items":null,"rank":100}]}}'
            NicoGiftEventLoader.upload_to_dynamodb(
                sample,
                timestamp,
            )

    @staticmethod
    def read_event_settings() -> List[EventSetting]:
        config = configparser.ConfigParser()
        config.read('settings.ini')
        event_settings = []
        for section in config.sections():
            event_settings.append(
                EventSetting(
                    section,
                    config.get(section, "ranking_json_url"),
                    config.get(section, "aws_access_key_id"),
                    config.get(section, "aws_secret_access_key"),
                    config.get(section, "aws_region"),
                    config.get(section, "s3_bucket"),
                    config.get(section, "s3_folder"),
                    config.get(section, "save_file_prefix")
                )
            )
        return event_settings

    @staticmethod
    def get_ranking_json(url: str) -> Optional[str]:
        response = requests.get(url, headers=NicoGiftEventLoader.make_http_header())
        return response.text if response.status_code == 200 else None

    @staticmethod
    def make_http_header():
        return {'User-Agent': USER_AGENT}

    @staticmethod
    def save_ranking_json(text: str, directory: str, filename: str) -> Optional[str]:
        fullpath = f"{directory}/{filename}"
        with open(fullpath, "wb") as f:
            f.write(text.encode('utf-8'))
        return fullpath

    @staticmethod
    def set_aws_environmental_values(access_key_id: str, secret_access_key: str, region: str):
        os.environ['AWS_ACCESS_KEY_ID'] = access_key_id
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_access_key
        os.environ['AWS_DEFAULT_REGION'] = region

    @staticmethod
    def backup_json_to_s3(directory: str, filename: str, s3_bucket: str, s3_folder: str):
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(s3_bucket)
        local_file = f"{directory}/{filename}"
        s3_key = f"{s3_folder}/{filename}"
        bucket.upload_file(local_file, s3_key)

    @staticmethod
    def upload_to_dynamodb(json_text: str, timestamp: int):
        dic = json.loads(json_text)
        # gift_event_id
        for entry_item in dic['data']['entry_items']:
            entry_item['timestamp'] = timestamp
            print(entry_item)
        dynamodb = boto3.resource('dynamodb')
        for tbl in dynamodb.tables.all():
            print(tbl.name)


loader = NicoGiftEventLoader()
loader.start()
