# SAVOLLAR BANKI — barcha savollar shu bitta faylda

POSITIONS = {
    "kassir": "🧾 Kassir",
    "sotuvchi": "🛒 Zal sotuvchisi",
    "omborchi": "📦 Omborchi",
    "farrosh": "🧹 Farrosh",
    "qoriqchi": "🛡️ Qo'riqchi",
}

# ---- BLOK 0: Avtofiltr ----

BLOCK0_AGE_OPTIONS = ["16 dan kichik", "16–17", "18–25", "26–35", "36–45", "45+"]
BLOCK0_AGE_REJECT = {"16 dan kichik"}
MINOR_AGE_RANGE = "16–17"
MINOR_SHIFT_LABEL = "2-smena (16:00–23:59)"

BLOCK0_BRANCH_OPTIONS = ["Haqqulobod", "To'rtko'l", "Ikkalasi ham"]

BLOCK0_SHIFT_OPTIONS = ["Ha", "Yo'q"]
BLOCK0_SHIFT_REJECT = {"Yo'q"}

BLOCK0_START_DATE_OPTIONS = ["Ertagayoq", "1 hafta ichida", "2 hafta+"]

# ---- BLOK 1: Faktlar (barcha lavozimlar) ----

BLOCK1_QUESTIONS = [
    {
        "id": "q1_1",
        "text": "Oxirgi ish joyingiz qayer edi va u yerda qancha muddat ishlagansiz?",
        "measures": "barqarorlik",
    },
    {
        "id": "q1_2",
        "text": "U yerdan nega ketgansiz?",
        "measures": "mas'uliyat — aybni boshqaga to'nkash = qizil bayroq",
    },
    {
        "id": "q1_3",
        "text": "Oxirgi 3 yilda jami nechta joyda ishladingiz?",
        "measures": "3+ = barqarorlik muammosi",
    },
    {
        "id": "q1_4",
        "text": "Agar oxirgi rahbaringizga qo'ng'iroq qilsak, u siz haqingizda nima deydi deb o'ylaysiz?",
        "measures": "halollik testi",
    },
]

# ---- BLOK 2: Lavozimga xos vaziyatli savollar ----

SITUATIONS = {
    "kassir": [
        {
            "id": "K1",
            "variants": [
                "Smena oxirida kassada 20 000 so'm kam chiqdi. Aniq qadamma-qadam nima qilasiz?",
                "Kunlik hisobotni yopayotganda kassada 20 000 so'm yetishmayotganini payqadingiz. Qadamma-qadam nima qilasiz?",
                "Ish kuni oxirida pul va cheklarni solishtirsangiz, 20 000 so'm kam chiqdi. Birinchi navbatda nima qilasiz, keyin-chi?",
            ],
            "measures": "Halollik, mas'uliyat. \"Yashiraman/o'zim qo'shib qo'yaman\" = qizil bayroq. To'g'ri yo'nalish: qayta sanash → rahbarga xabar",
            "auto_reject": False,
        },
        {
            "id": "K2",
            "variants": [
                "Navbat uzun, mijozlardan biri \"tezroq bo'ling!\" deb baqiryapti. Birinchi aytadigan gapingizni aynan yozing.",
                "Kassa oldida navbat uzayib ketdi, asabiylashgan mijoz ovozini ko'tarib \"nega bunchalik sekin ishlaysiz?!\" deb achchiqlanmoqda. Unga aynan nima deb javob berasiz?",
                "Band vaqtda navbatda turgan mijoz boshqalarga eshittirib \"xizmat juda sust!\" deb norozilik bildirdi. Birinchi aytadigan gapingizni aynan shu yerda yozing.",
            ],
            "measures": "Bosim ostida xotirjamlik, muloqot",
            "auto_reject": False,
        },
        {
            "id": "K3",
            "variants": [
                "Mijoz 50 000 so'mlik kupyura berdi, siz qaytim berdingiz, u \"men 100 ming berdim\" deyapti. Nima qilasiz?",
                "Hisob-kitobdan so'ng mijoz \"men sizga 100 ming so'm berdim, qaytimim noto'g'ri\" deb da'vo qilmoqda, siz esa 50 minglik olganingizga ishonchingiz komil. Qanday harakat qilasiz?",
                "Mijoz pul to'lagandan keyin qaytim kam berilganini aytib, aslida 100 minglik berganini da'vo qilyapti. Siz 50 minglik qabul qilganingizni aniq eslaysiz. Nima qilasiz?",
            ],
            "measures": "Protsedura bilishi, nizoni to'g'ri hal qilish. To'g'ri yo'nalish: xotirjam, kassani rahbar ishtirokida tekshirish, kamera",
            "auto_reject": False,
        },
        {
            "id": "K4",
            "variants": [
                "Yaqin tanishing keldi va \"menga chegirma qilib o'tkazib yubor\" deyapti. Javobingiz?",
                "Do'stingiz kassangizga keldi va \"mahsulotlarni to'liq to'lovsiz o'tkazib yubor, hech kim bilmaydi\" deb so'ramoqda. Qanday javob berasiz?",
                "Qarindoshingiz xarid qilib, \"menga pulini olmay, bepul o'tkazib yubor\" deb iltimos qilyapti. Javobingiz nima bo'ladi?",
            ],
            "measures": "Halollik, qoidaga sodiqlik. Har qanday \"o'tkazib yuboraman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "K5",
            "variants": [
                "Mijoz faqat non va sut oldi. Chekni oshirish uchun kassada turib nima taklif qilgan bo'lardingiz?",
                "Mijoz savatida faqat ikkita arzon mahsulot bor — non va sut. Kassada turib, chekni ko'paytirish uchun unga nima taklif qilgan bo'lardingiz?",
                "Mijoz kassaga faqat non va sut bilan keldi. Sotuvni oshirish uchun shu yerda unga qanday qo'shimcha taklif bergan bo'lardingiz?",
            ],
            "measures": "Sotuv instinkti (o'rtacha chek +30% strategiyasiga bog'lanadi)",
            "auto_reject": False,
        },
    ],
    "sotuvchi": [
        {
            "id": "S1",
            "variants": [
                "Mijoz baqiryapti: \"Sut muddati o'tgan ekan, pulimni qaytaring!\" Birinchi gapingizni aynan yozing.",
                "Mijoz qo'lida mahsulot bilan kelib, ovozini ko'tarib \"bu yogurtning muddati o'tib ketibdi, pulimni darhol qaytaring!\" deb talab qilmoqda. Unga aynan nima deysiz?",
                "G'azablangan mijoz \"siz menga muddati o'tgan mahsulot sotdingiz, pulimni qaytaring!\" deb zalda baqirmoqda. Birinchi aytadigan gapingizni aynan yozing.",
            ],
            "measures": "Nizo boshqaruvi, empatiya",
            "auto_reject": False,
        },
        {
            "id": "S2",
            "variants": [
                "Hamkasbingiz peshtaxtadan mahsulot olib cho'ntagiga solganini ko'rdingiz. Nima qilasiz?",
                "Ish vaqtida hamkasbingiz javondan mahsulot olib, uni to'lovsiz sumkasiga solib qo'yganini ko'rib qoldingiz. Nima qilasiz?",
                "Omborda hamkasbingiz mahsulotni yashirincha o'ziga olayotganini ko'rdingiz. Shu holatda nima qilasiz?",
            ],
            "measures": "Halollik. \"Hech nima qilmayman\" = avtomatik rad. To'g'ri: rahbarga xabar",
            "auto_reject": True,
        },
        {
            "id": "S3",
            "variants": [
                "Mijoz sizdan mahsulot haqida so'radi, siz bilmaysiz. Aniq nima qilasiz?",
                "Mijoz sizdan bir mahsulotning tarkibi haqida savol berdi, lekin javobini bilmaysiz. Aniq qanday harakat qilasiz?",
                "Mijoz noma'lum bir mahsulot haqida batafsil ma'lumot so'radi, siz esa javobini topa olmayapsiz. Shu vaziyatda aniq nima qilasiz?",
            ],
            "measures": "Rostgo'ylik + tashabbus. \"Bilmayman deb ketaman\" = past ball; \"bilib kelaman / biladigan hamkasbni chaqiraman\" = yuqori",
            "auto_reject": False,
        },
        {
            "id": "S4",
            "variants": [
                "Zalda navbat uzayib ketdi, kassir bitta, mijozlar norozi. Siz zaldasiz. Nima qilasiz?",
                "Kassada faqat bitta kassir ishlayapti, navbat uzunlashib, mijozlar g'ijinmoqda. O'zingiz zalda turibsiz. Qanday harakat qilasiz?",
                "Band soatda kassada navbat uzayib, mijozlar noroziligini bildira boshladi, kassir esa yolg'iz. Siz zalda ekansiz, nima qilasiz?",
            ],
            "measures": "Tashabbus, jamoaviylik",
            "auto_reject": False,
        },
        {
            "id": "S5",
            "variants": [
                "Mijoz arzon mahsulot izlayapti. Uni xafa qilmasdan qimmatroq lekin sifatliroq variantni qanday taklif qilasiz? So'zlaringizni yozing.",
                "Mijoz eng arzon mahsulotni izlayapti. Uni ranjitmasdan, sifatliroq va qimmatroq mahsulotni qanday taklif qilgan bo'lardingiz? Aynan gaplaringizni yozing.",
                "Mijoz byudjeti chegaralanganini aytib, arzon narx so'ramoqda. Uni xafa qilmay, sifatliroq variantni qanday taklif qilasiz? So'zlaringizni aynan yozing.",
            ],
            "measures": "Sotuv ko'nikmasi, upsell",
            "auto_reject": False,
        },
    ],
    "omborchi": [
        {
            "id": "O1",
            "variants": [
                "Yangi partiya keldi, nakladnoyda 100 dona, sanasangiz 96 dona chiqdi. Qadamma-qadam nima qilasiz?",
                "Yetkazib berilgan tovarni qabul qilayotganda hujjatda 100 dona ko'rsatilgan bo'lsa-da, sanab chiqqaningizda atigi 96 dona chiqdi. Qadamma-qadam nima qilasiz?",
                "Ta'minotchidan kelgan yukni tekshirayotganda, hujjatda 100 dona ko'rsatilgan bo'lsa-da, real sanoqda 96 ta chiqqanini aniqladingiz. Harakatlaringizni qadamma-qadam tushuntiring.",
            ],
            "measures": "Aniqlik, protsedura. To'g'ri: qayta sanash → hujjatlashtirish → rahbar/ta'minotchiga xabar",
            "auto_reject": False,
        },
        {
            "id": "O2",
            "variants": [
                "Omborda muddati tugashiga 5 kun qolgan mahsulot katta partiyasini ko'rdingiz. Nima qilasiz?",
                "Omborni tekshirayotganda muddati yaqin orada (5 kun ichida) tugaydigan katta hajmdagi mahsulotni topdingiz. Nima qilasiz?",
                "Inventarizatsiya paytida yaroqlilik muddati 5 kundan keyin tugaydigan ko'p miqdordagi mahsulotga duch keldingiz. Qanday harakat qilasiz?",
            ],
            "measures": "Proaktivlik, FIFO tushunchasi. To'g'ri: rahbarga xabar, zalga birinchi chiqarish, aksiya taklifi",
            "auto_reject": False,
        },
        {
            "id": "O3",
            "variants": [
                "Zaldan \"mahsulot tugadi, tez olib keling\" deyishdi, ayni paytda yangi mashina tushirilyapti. Qaysi birini qilasiz, nega?",
                "Siz yangi kelgan mashinani tushirayotgan paytingizda, zaldan shoshilinch ravishda bir mahsulot tugaganini va tezda olib kelish kerakligini aytishdi. Qaysi vazifani birinchi bajarasiz va nega?",
                "Bir vaqtning o'zida ham yuk mashinasini bo'shatish, ham zalga shoshilinch mahsulot olib chiqish kerak bo'lib qoldi. Qaysi birini ustuvor qilasiz va buning sababini tushuntiring.",
            ],
            "measures": "Ustuvorlik belgilash",
            "auto_reject": False,
        },
        {
            "id": "O4",
            "variants": [
                "Hamkasbingiz omborga begona odamni olib kirdi. Nima qilasiz?",
                "Ish vaqtida hamkasbingiz ruxsatsiz begona shaxsni ombor hududiga kiritganini ko'rdingiz. Nima qilasiz?",
                "Omborda ishlayotganingizda, hamkasbingiz tanimagan odamni ichkariga olib kirganini payqadingiz. Qanday harakat qilasiz?",
            ],
            "measures": "Xavfsizlik, qoidaga sodiqlik",
            "auto_reject": False,
        },
        {
            "id": "O5",
            "variants": [
                "Og'ir yuk tushirish paytida belingiz og'rib qoldi, smena tugashiga 3 soat bor. Nima qilasiz?",
                "Yuk tashish jarayonida belingizda kuchli og'riq paydo bo'ldi, smenaning tugashiga esa yana 3 soat qolgan. Nima qilasiz?",
                "Og'ir qutilarni ko'tarayotganda belingiz jiddiy og'riy boshladi, ish vaqti tugashiga 3 soat bor. Shu holatda nima qilasiz?",
            ],
            "measures": "Rostgo'ylik, o'zini asrash. \"Indamay ishlayveraman\" ham, \"tashlab ketaman\" ham past ball; to'g'ri: rahbarga aytish",
            "auto_reject": False,
        },
    ],
    "farrosh": [
        {
            "id": "F1",
            "variants": [
                "Zal o'rtasida mijoz shisha idishni tushirib yubordi, atrofda odam ko'p. Qadamma-qadam nima qilasiz?",
                "Savdo zalining markazida bir mijoz shisha bankani tushirib, u sinib ketdi, atrofda ko'plab odamlar yuribdi. Qadamma-qadam nima qilasiz?",
                "Mijozlar ko'p bo'lgan zalda kimdir shishali mahsulotni qo'lidan tushirib yubordi va u chil-chil bo'ldi. Harakatlaringizni qadamma-qadam tushuntiring.",
            ],
            "measures": "Xavfsizlik tushunchasi. To'g'ri: avval odamlarni ogohlantirish/to'sish, keyin tozalash",
            "auto_reject": False,
        },
        {
            "id": "F2",
            "variants": [
                "Siz endigina yuvgan joydan yana loy oyoq izlari qoldi. Ichingizda nima his qilasiz va nima qilasiz?",
                "Hozirgina tozalab bo'lgan polingizga darhol loy oyoq izlari tushib qoldi. Shu paytda ichingizda nima kechadi va nima qilasiz?",
                "Siz yuvib-tozalagan joy orqasidan darrov iflos qadam izlari paydo bo'ldi. O'zingizni qanday his qilasiz va keyingi harakatingiz qanday bo'ladi?",
            ],
            "measures": "Fe'l, sabr. Norozilik bildirish = qizil bayroq",
            "auto_reject": False,
        },
        {
            "id": "F3",
            "variants": [
                "Tozalash paytida javon ostidan pul (50 000 so'm) topib oldingiz. Nima qilasiz?",
                "Zalni tozalayotganingizda, peshtaxta ostidan 50 000 so'mlik pul topib oldingiz. Nima qilasiz?",
                "Tozalash jarayonida polda yotgan 50 000 so'mni ko'rib qoldingiz, atrofda hech kim yo'q. Nima qilasiz?",
            ],
            "measures": "Halollik. \"O'zimga olaman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "F4",
            "variants": [
                "Ish jadvalingizdagi hudud tugadi, smena tugashiga 1 soat bor. Nima qilasiz?",
                "O'zingizga belgilangan tozalash hududini tugatdingiz, ammo smenangiz tugashiga yana 1 soat qolgan. Shu vaqtda nima qilasiz?",
                "Kunlik vazifangizdagi barcha ishni erta bajarib bo'ldingiz, ish vaqtining tugashiga esa 1 soat bor. Nima qilasiz?",
            ],
            "measures": "Mehnatsevarlik, tashabbus",
            "auto_reject": False,
        },
        {
            "id": "F5",
            "variants": [
                "Mijoz sizdan \"guruch qayerda?\" deb so'radi. Javobingiz?",
                "Zalda tozalash ishlarini bajarayotganingizda, mijoz kelib \"guruch qayerda turibdi?\" deb so'ramoqda. Qanday javob berasiz?",
                "Siz ishlab turgan paytingizda mijoz yondashib, \"guruchni qayerdan topsam bo'ladi?\" deb so'radi. Javobingiz nima bo'ladi?",
            ],
            "measures": "Mijozga munosabat — farrosh ham do'kon yuzi. \"Bilmayman, men farroshman\" = past ball",
            "auto_reject": False,
        },
    ],
    "qoriqchi": [
        {
            "id": "G1",
            "variants": [
                "Chiqish eshigidagi signalizatsiya ishlab ketdi, mijoz \"men hech narsa olmadim\" deb ketishga urinmoqda. Aniq qadamma-qadam nima qilasiz?",
                "Chiqishda magnit darvoza signal berdi, mijoz esa \"men to'lovsiz hech narsa olmaganman\" deb tezda chiqib ketmoqchi. Qadamma-qadam qanday harakat qilasiz?",
                "Do'kondan chiqayotgan mijozda xavfsizlik darvozasi signal berdi, u esa \"bu xato, men hech narsa olmaganman\" deb da'vo qilib ketishga shoshilmoqda. Aniq nima qilasiz?",
            ],
            "measures": "Protsedura bilishi, nizoni to'g'ri hal qilish. To'g'ri yo'nalish: xushmuomala to'xtatish, ayblamaslik, rahbarga xabar",
            "auto_reject": False,
        },
        {
            "id": "G2",
            "variants": [
                "Tungi smenada tanish do'stingiz \"faqat besh daqiqaga kirib chiqaman\" deb yopiq do'konga kiritishni so'ramoqda. Javobingiz?",
                "Kechki/tungi smenada yaqin tanishingiz kelib, \"do'kon yopiq bo'lsa ham meni besh daqiqaga kiritib yubor\" deb iltimos qilmoqda. Javobingiz nima bo'ladi?",
                "Ish vaqtidan tashqari, do'stingiz yopiq do'konga \"tez kirib chiqaman, hech kim bilmaydi\" deb kirishni so'ramoqda. Qanday javob berasiz?",
            ],
            "measures": "Halollik, qoidaga sodiqlik. Har qanday \"kiritib yuboraman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "G3",
            "variants": [
                "Hamkasbingiz omborda mahsulot o'g'irlayotganini ko'rdingiz. Nima qilasiz?",
                "Kuzatuv paytida hamkasbingizning omborda mahsulotni yashirincha olib chiqib ketayotganini ko'rib qoldingiz. Nima qilasiz?",
                "Smenangiz davomida hamkasbingiz ombordan ruxsatsiz mahsulot olayotganini payqadingiz. Qanday harakat qilasiz?",
            ],
            "measures": "Halollik. \"Hech nima qilmayman\" = avtomatik rad. To'g'ri: rahbarga xabar",
            "auto_reject": True,
        },
        {
            "id": "G4",
            "variants": [
                "Ikki mijoz o'rtasida janjal boshlanib, ovoz balandlashdi, atrofda bolalar bor. Qadamma-qadam nima qilasiz?",
                "Zalda ikkita mijoz o'rtasida tortishuv chiqib, ovozlari baland ko'tarildi, yaqin atrofda bolali oilalar ham bor. Qadamma-qadam qanday harakat qilasiz?",
                "Navbat atrofida ikki mijoz orasida bahs kuchayib, janjalga aylanmoqda, yonida bolalar turibdi. Nima qilishingizni qadamma-qadam tushuntiring.",
            ],
            "measures": "Bosim ostida xotirjamlik, xavfsizlikni ta'minlash",
            "auto_reject": False,
        },
        {
            "id": "G5",
            "variants": [
                "Smena tugashiga 10 daqiqa qolganda yong'in signalizatsiyasi ishga tushdi. Nima qilasiz?",
                "Ish kuningiz tugashiga atigi 10 daqiqa qolganda, to'satdan yong'in signalizatsiyasi ovoz bera boshladi. Nima qilasiz?",
                "Smenangiz yakunlanishiga 10 daqiqa qolgan paytda yong'in ogohlantiruvchi signali ishga tushdi. Qanday harakat qilasiz?",
            ],
            "measures": "Favqulodda vaziyatga tayyorlik, mas'uliyat",
            "auto_reject": False,
        },
    ],
}

AUTO_REJECT_QUESTION_IDS = {"K4", "S2", "F3", "G2", "G3"}

OMBORCHI_HEALTH_QUESTION = "Og'ir yuk ko'tarishga sog'lig'ingiz yo'l qo'yadimi?"

# ---- BLOK 3: Media savollar ----

MEDIA_CONFIG = {
    "kassir": {"voice": True, "video": True},
    "sotuvchi": {"voice": True, "video": True},
    "omborchi": {"voice": True, "video": False},
    "farrosh": {"voice": False, "video": False},
    "qoriqchi": {"voice": True, "video": False},
}

VOICE_QUESTION_TEXT = (
    "🎤 Endi ovozli xabar yuboring (30–60 soniya). Tasavvur qiling: men do'konga "
    "birinchi marta kirgan mijozman. Menga o'zingiz yoqtirgan bitta mahsulotni "
    "ovoz bilan tavsiya qiling — xuddi zalda turgandek gapiring."
)

VIDEO_QUESTION_TEXT = (
    "🔴 Oxirgi qadam: dumaloq video yuboring (kamera tugmasini bosib turing, "
    "30–60 soniya). Videoda o'zingizni tanishtiring: ismingiz, nega aynan shu ishni "
    "xohlaysiz va nega aynan sizni tanlashimiz kerak."
)

# ---- BLOK 4: Motivatsiya (barcha lavozimlar) ----

BLOCK4_QUESTIONS = [
    {
        "id": "q4_1",
        "text": "Nega aynan Sharq Supermarket?",
        "measures": "do'kon haqida aniq biror narsa aytsa — kuchli signal",
    },
    {
        "id": "q4_2",
        "text": "6 oydan keyin o'zingizni qayerda ko'rasiz?",
        "measures": "",
    },
    {
        "id": "q4_3",
        "text": "O'zingizning eng zaif tomoningiz nima deb o'ylaysiz?",
        "measures": "\"zaif tomonim yo'q\" = qizil bayroq",
    },
    {
        "id": "q4_4",
        "text": "Bizga savolingiz bormi? Bo'lsa yozing, bo'lmasa \"yo'q\" deb yozing.",
        "measures": "faqat oylik so'ragan = past qiziqish; ish jarayoni haqida so'ragan = yuqori",
    },
]
