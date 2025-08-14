class Airport:
    def __init__(self, code, name, lat, long, reference):
        self.code = code
        self.name = name
        self.lat = lat
        self.long = long
        self.reference = reference
    def __repr__(self):
        return f"{self.code} - {self.name}"
class Route:
    def __init__(self, source_code: str, destination_code: str, route_name: str,reference):
        self.source_code = source_code
        self.destination_code = destination_code
        self.route_name = route_name
        self.reference = reference

    def __repr__(self):
        return f"{self.source_code} → {self.destination_code} via {self.route_name}"

manual_routes = [
    Route("YMHB", "YMLT", "H111","L1"),
    Route("YMLT", "YMMB","W218", "L1"),
    Route("YMLT", "YLTV", "W219", "L1"),
    Route("YMLT", "YMLT", "W105", "L1"),
    Route("YKII", "YMML", "W405", "L1"),
    Route("YKII", "YMMB", "W673"," L1"),
    Route("YMAV", "YMMB", "W635", "L1"),
    Route("YMML", "YLTV", "W449", "L1"),
    Route("YLTV", "YMES", "W449", "L1"),
    Route("YLTV", "YMLT", "W219"," L1"),
    Route("YMMB", "YMLT","W218", "L1"),
   
    Route("YMER", "YCOM", "W541", "L2"),
    Route("YMER", "YSCB", "W643"," L2"),
    Route("YMER", "YSNW", "W436"," L2"),
    Route("YMES", "YCOM", "W290", "L2"),
    Route("YMES", "YSCB", "W643", "L2"),
    Route("YMES", "YMAY", "W118"," L2"),
    Route("YMES", "YMNG", "W649", "L2"),
    Route("YHMT", "YMIA", "W584", "L2"),
    Route("YHMT", "YMTG", "W584", "L2"),
    Route("YMTG", "YPAD", "V259", "L2"),
    Route("YPAD", "YMIA", "H309", "L2"),
    Route("YPAD", "YSWH", "V255", "L2"),
    Route("YPAD", "YMML", "H345", "L2"),
    Route("YWHA", "YGTH", "J21", "L2"),
    Route("YWHA", "YPED", "W142", "L2"),
    Route("YWHA", "YMIA", "W448", "L2"),
    Route("YMIA", "YGTH", "W451", "L2"),
    Route("YMIA", "YSWH", "W481", "L2"),
    Route("YMIA", "YMTG", "W481", "L2"),
    Route("YMIA", "YHMT", "W584", "L2"),
    Route("YMIA", "YMTG", "W584", "L2"),
    Route("YMIA", "YMML", "V376", "L2"),
    Route("YMIA", "YMNG", "V173", "L2"),
    Route("YGTH", "YPKS", "W310", "L2"),
    Route("YGTH", "YBTH", "W386", "L2"),
    Route("YGTH", "YCWR", "H44", "L2"),
    Route("YGTH", "YSCB", "W266", "L2"),
    Route("YGTH", "YSWG", "W235", "L2"),
    Route("YPKS", "YBTH", "W460", "L2"),
    Route("YPKS", "YCWR", "W703", "L2"),
    Route("YBTH", "YSRI", "W460", "L2"),
    Route("YGLB", "YSNW", "W724", "L2"),
    Route("YSSY","YSRI","H530", "L3"),
    Route("YSSY","YSDU","V295","L3"),
    Route("YSSY","YSDU","V295","L3"),
    Route("YSSY","YWLM","V140","L3"),
    Route("YBTH","YPKS","W460","L3"),
    Route("YBTH","YMDG","W575","L3"),
    Route("YPKS","YSDU","W638","L3"),
    Route("YCOR","YPKS","W703","L3"),
    Route("YCOR","YMDG","W137","L3"),
    Route("YCOR","YBTH","W419","L3"),
    Route("YMND","YARM","W347","L3"),
    Route("YARM","YSTW","V258","L3"),
    Route("YWLM","YIVR","V779","L3"),
    Route("YWLM","YSSY","V140","L3"),
    Route("YMDG","YBTH","W575","L3"),
    Route("YMDG","YCOR","W137","L3"),
    Route("YMDG","YSDU","W785","L3"),
    Route("YMDG","YSTW","H66","L3"),
    Route("YSDU","YWLG","W822","L3"),
    Route("YSDU","YPKS","W638","L3"),
    Route("YPMQ","YSTW","W821","L3"),
    Route("YPMQ","YCFS","V652","L3"),
    Route("YPMQ ","YARM","W381","L3"),
    Route("YSTW","YPMQ","W821","L3"),
    Route("YSTW","YCFS","W330","L3"),
    Route("YSTW","YARM","W786","L3"),
    Route("YSTW","YIVR","W684","L3"),
    Route("YSTW","YMOR","W318","L3"),
    Route("YSTW","YBBN","V258","L3"),
    Route("YSTW","YWLG","W514","L3"),
    Route("YSTW","YMDG","H66","L3"),
    Route("YWLG","YSGE","W353","L3"),
    Route("YWLG","YIVR","W623","L3"),
    Route("YWLG","YSDU","W822","L3"),
    Route("YIVR","YGFN","W353","L3"),
    Route("YIVR","YBOK","W207","L3"),
    Route("YIVR","YWLG","W623","L3"),
    Route("YGFN","YBNA","V652", "L3"),
    
]



sample_airports = [
        Airport("YHMT", "Hamilton ", -37.647982744108525, 142.05926567800736, "L1"),
        Airport("YMTG", "Mount Gambier ", -37.74426749838051, 140.78283069783433, "L1"),
        
       
        Airport("YMAV", "Avalon ",-38.03903211523271, 144.46840494906976, "L1"),
        Airport("YKII", "King Island ", -39.879687334185256, 143.8818384177821, "L1"),
        Airport("YMES", "East Sale ", -38.10538647309576, 147.12868355367507, "L1"),
        Airport("YLTV", "Latrobe Valley ", -38.21198953077352, 146.47284563586777, "L1"),
        Airport("YWYY", "Wynyard ", -40.99332991000915, 145.7256267691996, "L1"),
        Airport("YMHB", "Hobart ", -42.83754020572746, 147.51172801350043, "L1"),
        Airport("YMLT", "Launceston ", -41.54297348998329, 147.21051998087307, "L1"),
        Airport("YWHA", "Whyalla ",-33.05225363994528, 137.52164473804072, "L2"),
        
      
       
        Airport("YMIA", "Mildura ", -34.23041793161704, 142.08459262461383, "L2"),
        Airport("YSWH", "Swan Hill ",-35.37806144056377, 143.5399509707127, "L2"),
        
        
        Airport("YSHT", "Shepparton ", -36.42655501573895, 145.39056794008383, "L2"),
       
        Airport("YMES", "East Sale ",-38.10538647309576, 147.12868355367507, "L2"),
        Airport("YLTV", "Latrobe Valley ", -38.21198953077352, 146.47284563586777, "L2"),
        Airport("YMMB", "Moorabbin ", -37.97603247087848, 145.09467373747825, "L2"),
        Airport("YSWG", "Wagga Wagga ", -35.159130478567675, 147.46193801464656, "L2"),
        Airport("YCOR", "Corowa ", -35.98859804614794, 146.35583466518807, "L2"),
       
        Airport("YPKS", "Parkes ", -33.138198580742745, 148.23346370735584, "L2"),
        Airport("YGTH", "Griffith ",-34.25533309196504, 146.06261713995994, "L2"),
        Airport("YMTG", "Mount Gambier ", -37.744275982215804, 140.78275559598106, "L2"),
        Airport("YCWR", "Cowra ", -33.844998049470796, 148.65053965157543, "L2"),
       
       
        
       
        Airport("YSHL", "Shellharbour ", -34.56021654495789, 150.7903899444761, "L2"),
        
        
        Airport("YCOM", "Cooma ", -36.292064139549296, 148.97031722473116, "L2"),
        Airport("YMER", "Merimbula ", -36.90966890755481, 149.9021018094228, "L2"),
        Airport("YMCO", "Mallacoota ", -37.59877136017921, 149.7228752806275, "L2"),
       
       
        Airport("YHMT", "Hamilton ", -37.64810173391871, 142.0591476806306, "L2"),
        Airport("YSHT", "Shepparton ",-36.42647732210465, 145.39066449960944, "L2"),
        Airport("YROM", "Roma ", -26.543959398766567, 148.77921118040965, "L3"),
        Airport("YSGE", "St George ",-28.046801296368827, 148.5945145598291, "L3"),
        Airport("YWLG", "Walgett ", -30.030484749039385, 148.12301648021102, "L3"),
        Airport("YSDU", "Dubbo  ", -32.21870733806678, 148.56979729752172, "L3"),
        Airport("YPKS", "Parkes ", -33.138198580742745, 148.23367828407945, "L3"),
        Airport("YCWR", "Cowra ", -33.84514062224538, 148.65059329575635, "L3"),
        Airport("YTOG", "Togo Station ",-30.0821991, 149.5319977, "L3"),
        Airport("YCTA", "Coolatai ",-29.144167, 150.724722, "L3"),
        Airport("YBBN", "Narrabri ", -30.318446060832635, 149.82894659742354, "L3"),
        Airport("YMOR", "Moree ", -29.495875265330454, 149.85006048203778   , "L3"),
        Airport("YMDG", "Mudgee ", -32.5640790679433, 149.61615550917816, "L3"),
        Airport("YBTH", "Bathurst ", -33.4137212844603, 149.65508013991354, "L3"),
        

        Airport("YSTW", "Tamworth ",-31.084251932642843, 150.8484596262986, "L3"),
        Airport("YIVR", "Inverell ",-29.883782465778193, 151.14096082438454, "L3"),
        
        Airport("YCBB", "Coonabarabran  ",-31.33230483971066, 149.26959198213052, "L3"),
       

        Airport("YBNA", "Ballina  ", -28.83727421779521, 153.55627270898842, "L3"),
      
        Airport("YCFS", "Coffs Harbour ", -30.322769036588543, 153.115804337898, "L3"),
   
       
        
       
      
        Airport("YBCS", "Cairns ",-16.87753671625661, 145.74982790665905, "L4"),
        Airport("YBTL", "Townsville ", -19.256185239012645, 146.77060803927975, "L4"),
        Airport("YCSV", "Collinsville ", -20.59933618075106, 147.85210577980186, "L4"),
        Airport("YBPN", "Whitsunday Coast ", -20.492043732942832, 148.55836235281507, "L4"),
       
        
        Airport("YGLT", "Gladstone ", -23.871702738379643, 151.22450203879168, "L4"),
        
       
        Airport("YIVR", "Inverell ", -29.8836894426713, 151.14085353602272, "L4"),
        
        Airport("YROM", "Roma ", -26.54381996085789, 148.77914949992592, "L4"),
        Airport("YEML", "Emerald ", -23.568755084553896, 148.17442714129572, "L4"),
        Airport("YHUG", "Hughenden ", -20.816424439416096, 144.2270591356288, "L4"),
        Airport("YLRE", "Longreach ", -23.43759139345575, 144.27412390689446, "L4"),
        Airport("YBCV", "Charleville ",-26.41321410021968, 146.2591734702542, "L4"),
        Airport("YSGE", "St George ", -28.04673506725657, 148.5944931242954, "L4"),
        Airport("YWLG", "Walgett ", -30.030605500621483, 148.12301648021102, "L4"),
        Airport("YMOR", "Moree ", -29.495996662945853, 149.8500390243654, "L4"),
        Airport("YBBN", "Narrabri ", -30.318353445929123, 149.828914410915, "L4"),
        Airport("YCMU", "Cunnamulla ", -28.031143649497167, 145.62595822614787, "L4"),
        Airport("YWDH", "Windorah ", -25.41162944463946, 142.66364346835653, "L4"),
        Airport("YBMA", "Mount Isa ", -20.667544506725573, 139.49166869514892, "L4"),
        Airport("YPKS", "Parkes ", -33.13824349992342, 148.2335388092091, "L5"),
        Airport("YSDU", "Dubbo  ", -32.21875272205755, 148.56966855148755, "L5"),
        Airport("YWLG", "Walgett ",-30.030475460450056, 148.12300575137485, "L5"),
        Airport("YSGE", "St George ", -28.04673506725657, 148.5944931242954, "L5"),
        Airport("YBCV", "Charleville ", -26.413127620591354, 146.25900180887533, "L5"),
        Airport("YHUG", "Hughenden ",-20.81643446791445, 144.22724152584385, "L5"),
        Airport("YGTH", "Griffith ",-34.25520894290226, 146.06247766508957, "L5"),
        Airport("YCBA", "Cobar ", -31.537254490587994, 145.79743622261563, "L5"),
        Airport("YBKE", "Bourke ", -30.041573486449646, 145.9496592783584, "L5"),
        Airport("YCMU", "Cunnamulla ", -28.03106788738615, 145.62602259916494, "L5"),
        Airport("YBCV", "Longreach ",  -23.43750280065669, 144.27423119525625, "L5"),
        Airport("YWDH", "Windorah ", -25.411823260519785, 142.66348253581384, "L5"),
        Airport("YBHI", "Broken Hill ", -31.998565711747247, 141.47027941100154, "L5"),
        Airport("YMIA", "Mildura ", -34.230559858040095, 142.08448533625202, "L5"),
        Airport("YOOM", "Moomba ", -28.101169302073234, 140.19794386291895, "L5"),
        Airport("YBDV", "Birdsville ", -25.89684612213138, 139.3510359088522, "L5"),
        Airport("YBOU", "Boulia ", -22.90834638302379, 139.8995042087263, "L5"),
        Airport("YBMA", "Mount Isa ", -20.667584660208487, 139.49166869514892, "L5"),
        Airport("YCCY", "Cloncurry ", -20.668685589407445, 140.50840504726176, "L5"),
        Airport("PHD", "Port Hedland  ", -20.37791280403984, 118.63177672397467, "L6"),
        Airport("YTNK", "Tennant Creek ", -19.640919412642052, 134.18461655278466, "L6"),
        Airport("YBMA", "Mount Isa ", -20.667584660208487, 139.49166869514892, "L6"),
        Airport("YCCY", "Cloncurry ", -20.668605283013125, 140.50843723377028, "L6"),
        Airport("YHUD", "Hughenden ", -20.81648461039614, 144.22709132213734, "L6"),
        Airport("YBRM", "Broome ", -17.952421598849195, 122.23384659690832, "L6"),
        Airport("YDBY", "Derby ",-17.369702871103858, 123.66259149503632, "L6"),
        Airport("YCSP", "Curtin Springs ",-17.587595936873875, 123.82604126991357, "L6"),
        Airport("YARG", "Argyle ", -16.6390834102357, 128.4514819304586, "L6"),
        Airport("YHLC", "Halls Creek ", -18.231422465655506, 127.66870710855565, "L6"),
        Airport("YNTN", "Normanton ", -17.685152816806898, 141.07298962388245, "L6"),
        
        Airport("YPKU", "Kununurra ", -15.78370255016467, 128.7127438968412, "L6"),
        Airport("YPTN", "Tindal ", -14.512792375041146, 132.3652063102967, "L6"),
        Airport("YGTE", "Groote Eylandt ", -13.973612129747846, 136.45762509679085, "L6"),
        Airport("YCOE", "Coen ",-13.764147868272925, 143.1181198986386, "L6"),
        Airport("YLHR", "Lockhart River ", -12.784822042144501, 143.3067168949071, "L6"),
        Airport("YBWP", "Weipa ",-12.680550710400894, 141.92437133908547, "L6"),
        Airport("YPGV", "Gove ", -12.269593696361744, 136.82246982373096, "L6"),
        Airport("YMGD", "Maningrida ", -12.054725912229845, 134.23225989488955, "L6"),
       
        Airport("YHOD", "Hooker Creek ", -18.334553167270553, 130.63603037972274, "L6"),
        Airport("YHID", "Horn Island ", -10.59090634465989, 142.2945386660208, "L6"),
        Airport("YHLC", "Halls Creek ", -18.231534558423313, 127.66869637971945, "L7"),
        Airport("YWBR", "Warburton", -26.12553254030709, 126.58333327469452, "L7"),
        Airport("YFRT", "Forrest", -30.84666844031376, 128.11446432257992, "L7"),
        Airport("YHOD", "Hooker Creek", -18.33464482501615, 130.6359552778695, "L7"),
        Airport("YAYE", "Ayers Rock", -25.190406584190825, 130.97623950882132, "L7"),
        Airport("YCBP", "Coober Pedy", -29.040703636406697, 134.7218267801622, "L7"),
        Airport("YCDU", "Ceduna", -32.12382103886972, 133.70176823984437, "L7"),
        Airport("YPLC", "Port Lincoln", -34.603691371294325, 135.8745396939452, "L7"),
        Airport("YPWR", "Woomera", -31.145940604521503, 136.81253898026756, "L7"),
        Airport("YBAS", "Alice Springs", -23.80163262127604, 133.9032980262685, "L7"),
        Airport("YTNK", "Tennant Creek", -19.640858784989415, 134.1846058239485, "L7"),
        Airport("YLEC", "Leigh Creek", -30.597383429597876, 138.4223243820929, "L7"),
        Airport("YPED", "Edinburgh", -33.48349259204509, 138.64399790517135, "L7"),
        Airport("YWHA", "Whyalla", -33.05223565469144, 137.52165546687692, "L7"),
        Airport("YESP", "Esperance ", -33.68257177466934, 121.830466482256, "L8"),
        Airport("YPKG", "Kalgoorlie-Boulder ", -30.785139331177707, 121.45790479374061, "L8"),
        Airport("ICAO", "RAAF Base Curtin",-17.587647073508073, 123.8259232527156, "L8"),
        Airport("YDBY", "Derby ", -17.36967215235245, 123.66243056249363, "L8"),
        Airport("YABA", "Albany ", -34.902410813326156, 117.7641616093025, "L8"),
        Airport("YLEO", "Leonora ", -28.87913293370292, 121.31673801770397, "L8"),
        Airport("YLST", "Leinster ", -27.838544610330164, 120.7038471954494, "L8"),
        Airport("YWLU", "Wiluna ", -26.62757506775238, 120.22050036841051, "L8"),
        Airport("YNWN", "Newman ", -23.41595857165631, 119.80229608176387, "L8"),
        Airport("YBRM", "Broome ", -17.952309327546406, 122.23366420669328, "L8"),
        Airport("YPPD", "Port Hedland  ", -20.37782228754356, 118.63178745281085, "L8"),
        Airport("YPBO", "Paraburdoo ", -23.17364023120617, 117.74798698360733, "L8"),
        Airport("YMEK", "Meekatharra ", -26.610831522776493, 118.5459620395738, "L8"),
        Airport("YMOG", "Mount Magnet ", -28.11586768299786, 117.84324360895394, "L8"),
        Airport("YCUN", "Cunderdin ", -31.622529714565214, 117.21752970727533, "L8"),
        Airport("YBLN", "Busselton Margaret River ", -33.685759999551664, 115.39871589389442, "L8"),
        Airport("YPJT", "Jandakot ", -32.09388995699968, 115.8790784379896, "L8"),
        Airport("YPEA", "RAAF Base Pearce", -31.667446803024184, 116.02927508214805, "L8"),
        Airport("YGIN", "Gingin ", -31.462585287347537, 115.85886949022037, "L8"),
        Airport("YBRM", "Beermullah ", -31.267708764732273, 115.83883021096337, "L8"),
        Airport("YGEL", "Geraldton ", -28.79601686502884, 114.70237792433117, "L8"),
        
        Airport("YPLM", "Learmonth ", -22.239796342113156, 114.09415311055321, "L8"),
        Airport("YPKA", "Karratha ", -20.708488939017283, 116.7702464970038, "L8"),
]

airports = [
        Airport("YHMT", "Hamilton ",  -37.5075, 142.0972, "L1"),
        Airport("YMTG", "Mount Gambier ", -37.6827, 140.7719, "L1"),
       
         Airport("YMAV", "Avalon ",-37.8488, 144.6075, "L1"),
        Airport("YKII", "King Island", -39.8634,  144.0967, "L1"),
        Airport("YMES", "East Sale ", -37.8944, 147.3706, "L1"),
        Airport("YLTV", "Latrobe Valley ",-38.0027,  146.6949, "L1"),
        Airport("YWYY", "Wynyard ", -40.9592,145.9369, "L1"),
        Airport("YMHB", "Hobart ",  -42.8357, 147.7441, "L1"),
        Airport("YMLT", "Launceston ", -41.5302, 147.4352, "L1"),
        Airport("YWHA", "Whyalla ", -33.0524 ,137.5218, "L2"),
        Airport("YPED", "RAAF Base Edinburgh", -34.701997192, 138.618664192, "L2"),
       
        Airport("YMIA", "Mildura ", -33.9723, 142.2687, "L2"),
        Airport("YSWH", "Swan Hill ", -35.0174 ,143.7503, "L2"),
       
       
        
        
        Airport("YMES", "East Sale ",-37.4836 , 147.2964, "L2"),
        Airport("YLTV", "Latrobe Valley ",  -37.5576, 146.6345, "L2"),
        Airport("YMMB", "Moorabbin ",  -37.3461,  145.2859, "L2"),
        Airport("YSWG", "Wagga Wagga ",-34.8544 ,147.7084147, "L2"),
        Airport("YCOR", "Corowa ", -35.5769 ,146.5714, "L2"),
       
        
        Airport("YPKS", "Parkes ", -32.9902 ,148.5873, "L2"),
        Airport("YGTH", "Griffith ",-33.9803 ,146.3144, "L2"),
        Airport("YMTG", "Mount Gambier ", -37.1931,  141.1057, "L2"),
        Airport("YCWR", "Cowra ",  -33.6718 ,148.9911, "L2"),
        
      
        
        
        Airport("YSHL", "Shellharbour ",  -35.9558,145.5963, "L2"),
       
        
        Airport("YCOM", "Cooma ",  -35.9702, 149.1367, "L2"),
        Airport("YMER", "Merimbula ", -36.4920,  150.0293, "L2"),
        Airport("YMCO", "Mallacoota ",  -37.1187, 149.8178, "L2"),
       
       
       
        Airport("YHMT", "Hamilton ",  -37.0837, 142.3224, "L2"),
        Airport("YSHT", "Shepparton ",  -35.9536,145.5853, "L2"),
        Airport("YROM", "Roma ",  -26.0469,148.0133, "L3"),
        Airport("YSGE", "St George ", -27.7516,  147.6837, "L3"),
        Airport("YWLG", "Walgett ",  -29.9454, 146.9202, "L3"),
        Airport("YSDU", "Dubbo  ", -32.3196, 147.6178, "L3"),
        Airport("YPKS", "Parkes ", -33.3122, 147.0905, "L3"),
        Airport("YCWR", "Cowra ",  -34.0663, 147.7112, "L3"),
        Airport("YTOG", "Togo Station ",-30.0073, 149.1916, "L3"),
     Airport("YCTA", "Coolatai ", -29.0177, 151.1472, "L3"),
        Airport("YBBN", "Narrabri ", -30.2875, 149.6475, "L3"),
        Airport("YMOR", "Moree ", -29.3774, 149.7052, "L3"),
        Airport("YMDG", "Mudgee ", -32.6717, 149.1998, "L3"),
        Airport("YBTH", "Bathurst ", -33.6055, 149.2712, "L3"),
  
      
        Airport("YSTW", "Tamworth ", -31.1188, 151.2378, "L3"),
        Airport("YIVR", "Inverell ", -29.8359, 151.8091, "L3"),
       
       
       
   
       
        
        Airport("YBNA", "Ballina  ", -28.7556, 155.7944, "L3"),
       
        Airport("YCFS", "Coffs Harbour ", -30.3800, 154.951, "L3"),
        
       
        
      
       
        
        Airport("YBCS", "Cairns ",  -15.9244,145.2173, "L4"),
        Airport("YBTL", "Townsville ",  -18.5629, 146.4093, "L4"),
        Airport("YCSV", "Collinsville ", -19.9863, 147.6151, "L4"),
        Airport("YBPN", "Proserpine ", -19.8313, 148.2605, "L4"),
       Airport("YGLT", "Gladstone ",  -23.4078, 151.0455, "L4"),
      Airport("YIVR", "Inverell ", -29.8466, 151.2762, "L4"),
        Airport("YROM", "Roma ", -26.4460, 148.9005, "L4"),
        Airport("YEML", "Emerald ", -23.2742, 148.1314, "L4"),
        Airport("YHUG", "Hughenden ", -20.5531, 144.0953, "L4"),
        Airport("YLRE", "Longreach ", -23.4280, 144.4070, "L4"),
        Airport("YBCV", "Charleville ",  -26.4902, 146.5192, "L4"),
        Airport("YSGE", "St George ", -28.0526, 148.8455, "L4"),
        Airport("YWLG", "Walgett ",  -30.1499,148.5406, "L4"),
        Airport("YMOR", "Moree ", -29.5113, 150.0870, "L4"),
        Airport("YBBN", "Narrabri ", -30.3634, 150.1227, "L4"),
        Airport("YCMU", "Cunnamulla ",  -28.2342, 146.0934, "L4"),
        Airport("YWDH", "Windorah ", -25.7084,  143.0859, "L4"),
        Airport("YBMA", "Mount Isa ", -20.9204, 139.4769, "L4"),
        Airport("YBMA", "Cloncurry ", -20.8126, 140.4657, "L4"),
        Airport("YPKS", "Parkes ",  -33.1697, 148.3594, "L5"),
        Airport("YSDU", "Dubbo  ", -32.4217, 148.8757, "L5"),
        Airport("YWLG", "Walgett ",-30.4250, 148.7109, "L5"),
        Airport("YSGE", "St George ", -28.6327, 149.6008, "L5"),
        Airport("YBCV", "Charleville ", -26.9319, 147.0630, "L5"),
        Airport("YHUG", "Hughenden ",  -21.3968, 145.3931, "L5"),
        Airport("YGTH", "Griffith ", -33.9935, 145.7913, "L5"),
        Airport("YCBA", "Cobar ",  -31.5832,  145.8600, "L5"),
        Airport("YBKE", "Bourke ",  -30.2543, 146.2390, "L5"),
        Airport("YCMU", "Cunnamulla ",  -28.3624, 146.1484, "L5"),
        Airport("YBCV", "Longreach ",   -23.9461, 145.1514, "L5"),
        Airport("YWDH", "Windorah ",  -25.6935, 142.9431, "L5"),
        Airport("YBHI", "Broken Hill ",  -31.7095,  140.9354, "L5"),
        Airport("YMIA", "Mildura ",  -33.7289, 141.4105, "L5"),
        Airport("YOOM", "Moomba ", -28.0914, 139.7900, "L5"),
        Airport("YBDV", "Birdsville ",  -25.9778, 138.9441, "L5"),
        Airport("YBOU", "Boulia ",  -23.1479,  139.8257, "L5"),
        Airport("YBMA", "Mount Isa ",  -20.9358, 139.4714, "L5"),
        Airport("YCCY", "Cloncurry ",  -20.9666 , 140.7486, "L5"),
         Airport("PHD", "Port Hedland  ",  -18.1876, 117.8174, "L6"),
        Airport("YTNK", "Tennant Creek ",  -19.7564, 133.3411, "L6"),
        Airport("YBMA", "Mount Isa ", -22.2789,  138.4167, "L6"),
        Airport("YCCY", "Cloncurry ", -22.5633, 139.3726, "L6"),
        Airport("YHUD", "Hughenden ",  -23.7250, 143.0310, "L6"),
        Airport("YBRM", "Broome ",  -15.2630,  121.5417, "L6"),
        Airport("YDBY", "Derby ", -14.6314, 123.1348, "L6"),
        Airport("YCSP", "Curtin  ",-15.0350, 123.2721, "L6"),
        Airport("YARG", "Argyle ", -14.4347,  128.0347, "L6"),
        Airport("YHLC", "Halls Creek ",  -16.5678,  127.0514, "L6"),
        Airport("YNTN", "Normanton ", -18.6775, 140.5371, "L6"),
        
        Airport("YPKU", "Kununurra ",  -13.2827, 128.4521, "L6"),
        Airport("YPTN", "Tindal ", -12.2649, 132.3853, "L6"),
        Airport("YGTE", "Groote Eylandt ", -12.4151, 136.6095, "L6"),
        Airport("YCOE", "Coen ",  -13.8487, 143.4045, "L6"),
        Airport("YLHR", "Lockhart River ", -12.5117, 143.8550, "L6"),
        Airport("YBWP", "Weipa ", -11.9748, 142.4707, "L6"),
        Airport("YPGV", "Gove ",  -10.0446, 137.2852, "L6"),
        Airport("YMGD", "Maningrida ", -9.1889, 134.6924, "L6"),
        Airport("YCBB", "Coonabarabran  ",-31.3747, 148.7164, "L3"),
        Airport("YHOD", "Hooker Creek",  -17.2676,  130.0152, "L6"),
        Airport("YHID", "Horn Island ",  -9.0912, 143.2617, "L6"),
        Airport("YHLC", "Halls Creek ", -18.1563,  127.2986, "L7"),
        Airport("YWBR", "Warburton",  -31.6534, 137.2412, "L7"),
        Airport("YFRT", "Forrest",  -31.0414, 127.5718, "L7"),
        Airport("YHOD", "Hooker Creek",  -18.3441,  130.9680, "L7"),
        Airport("YAYE", "Ayers Rock",  -25.4532, 131.0449, "L7"),
        Airport("YCBP", "Coober Pedy",  -29.4539, 135.1593, "L7"),
        Airport("YCDU", "Ceduna",  -32.3846, 133.7421, "L7"),
        Airport("YPLC", "Port Lincoln",  -34.7867, 135.9119, "L7"),
        Airport("YPWR", "Woomera", -31.6347,  137.2302, "L7"),
        Airport("YBAS", "Alice Springs", -24.2670,  134.5935, "L7"),
        Airport("YTNK", "Tennant Creek",   -19.9088,135.3406, "L7"),
        
        Airport("YLEC", "Leigh Creek", -31.2316,  139.1473, "L7"),
        Airport("YPED", "Edinburgh", -35.0997, 138.8287, "L7"),
        Airport("YWHA", "Whyalla",  -33.4956,  137.8290, "L7"),
       
        Airport("YWBR", "Warburton",   -26.3500,  125.8813, "L7"),
        Airport("YESP", "Esperance ", -33.5105, 121.8274, "L8"),
        Airport("YPKG", "Kalgoorlie ", -30.9493,  121.4209, "L8"),
        Airport("ICAO", "Curtin",-18.4119, 123.2446, "L8"),
        Airport("YDBY", "Derby ", -18.1459,  123.0579, "L8"),
        Airport("YABA", "Albany ", -34.7642, 118.5370, "L8"),
        Airport("YLEO", "Leonora ", -29.2329, 121.2076, "L8"),
        Airport("YLST", "Leinster ", -28.2802, 120.6244, "L8"),
        
        Airport("YWLU", "Wiluna ",  -27.2107, 120.1520, "L8"),
        
        Airport("YNWN", "Newman ",  -24.1919, 119.6136, "L8"),
        Airport("YBRM", "Broome International ", -18.8179, 121.6846, "L8"),
        Airport("YPPD", "Port Hedland International ",  -21.3457, 118.4052, "L8"),
        Airport("YPBO", "Paraburdoo ",  -24.0715,  117.7295, "L8"),
        Airport("YMEK", "Meekatharra ", -27.2351,  118.6523, "L8"),
        Airport("YMOG", "Mount Magnet ", -28.6424, 118.1305, "L8"),
        
        Airport("YCUN", "Cunderdin ", -31.8706, 117.8284, "L8"),
        
        Airport("YBLN", "Busselton Margaret River ", -33.7719, 116.4308, "L8"),
        Airport("YPJT", "Jandakot ", -32.3707,   116.7078, "L8"),
        Airport("YPEA", "Pearce",  -31.9568,  116.7709, "L8"),
        Airport("YGIN", "Gingin ", -31.8052, 116.6391, "L8"),
        Airport("YBRM", "Beermullah ", -31.6358,  116.6034, "L8"),
        Airport("YGEL", "Geraldton ", -29.4635,  115.4169, "L8"),
        
        Airport("YPLM", "Learmonth ",  -23.4078, 114.2688, "L8"),
        Airport("YPKA", "Karratha ", -21.7748,116.6748, "L8"),
]
