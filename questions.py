# SAVOLLAR BANKI — barcha savollar shu bitta faylda

POSITIONS = {
    "kassir": "🧾 Kassir",
    "sotuvchi": "🛒 Zal sotuvchisi",
    "omborchi": "📦 Omborchi",
    "farrosh": "🧹 Farrosh",
    "qoriqchi": "🛡️ Qo'riqchi",
}

# ---- BLOK 0: Avtofiltr ----

BLOCK0_AGE_OPTIONS = ["18 dan kichik", "18–25", "26–35", "36–45", "45+"]
BLOCK0_AGE_REJECT = {"18 dan kichik"}

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
            "text": "Smena oxirida kassada 20 000 so'm kam chiqdi. Aniq qadamma-qadam nima qilasiz?",
            "measures": "Halollik, mas'uliyat. \"Yashiraman/o'zim qo'shib qo'yaman\" = qizil bayroq. To'g'ri yo'nalish: qayta sanash → rahbarga xabar",
            "auto_reject": False,
        },
        {
            "id": "K2",
            "text": "Navbat uzun, mijozlardan biri \"tezroq bo'ling!\" deb baqiryapti. Birinchi aytadigan gapingizni aynan yozing.",
            "measures": "Bosim ostida xotirjamlik, muloqot",
            "auto_reject": False,
        },
        {
            "id": "K3",
            "text": "Mijoz 50 000 so'mlik kupyura berdi, siz qaytim berdingiz, u \"men 100 ming berdim\" deyapti. Nima qilasiz?",
            "measures": "Protsedura bilishi, nizoni to'g'ri hal qilish. To'g'ri yo'nalish: xotirjam, kassani rahbar ishtirokida tekshirish, kamera",
            "auto_reject": False,
        },
        {
            "id": "K4",
            "text": "Yaqin tanishing keldi va \"menga chegirma qilib o'tkazib yubor\" deyapti. Javobingiz?",
            "measures": "Halollik, qoidaga sodiqlik. Har qanday \"o'tkazib yuboraman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "K5",
            "text": "Mijoz faqat non va sut oldi. Chekni oshirish uchun kassada turib nima taklif qilgan bo'lardingiz?",
            "measures": "Sotuv instinkti (o'rtacha chek +30% strategiyasiga bog'lanadi)",
            "auto_reject": False,
        },
    ],
    "sotuvchi": [
        {
            "id": "S1",
            "text": "Mijoz baqiryapti: \"Sut muddati o'tgan ekan, pulimni qaytaring!\" Birinchi gapingizni aynan yozing.",
            "measures": "Nizo boshqaruvi, empatiya",
            "auto_reject": False,
        },
        {
            "id": "S2",
            "text": "Hamkasbingiz peshtaxtadan mahsulot olib cho'ntagiga solganini ko'rdingiz. Nima qilasiz?",
            "measures": "Halollik. \"Hech nima qilmayman\" = avtomatik rad. To'g'ri: rahbarga xabar",
            "auto_reject": True,
        },
        {
            "id": "S3",
            "text": "Mijoz sizdan mahsulot haqida so'radi, siz bilmaysiz. Aniq nima qilasiz?",
            "measures": "Rostgo'ylik + tashabbus. \"Bilmayman deb ketaman\" = past ball; \"bilib kelaman / biladigan hamkasbni chaqiraman\" = yuqori",
            "auto_reject": False,
        },
        {
            "id": "S4",
            "text": "Zalda navbat uzayib ketdi, kassir bitta, mijozlar norozi. Siz zaldasiz. Nima qilasiz?",
            "measures": "Tashabbus, jamoaviylik",
            "auto_reject": False,
        },
        {
            "id": "S5",
            "text": "Mijoz arzon mahsulot izlayapti. Uni xafa qilmasdan qimmatroq lekin sifatliroq variantni qanday taklif qilasiz? So'zlaringizni yozing.",
            "measures": "Sotuv ko'nikmasi, upsell",
            "auto_reject": False,
        },
    ],
    "omborchi": [
        {
            "id": "O1",
            "text": "Yangi partiya keldi, nakladnoyda 100 dona, sanasangiz 96 dona chiqdi. Qadamma-qadam nima qilasiz?",
            "measures": "Aniqlik, protsedura. To'g'ri: qayta sanash → hujjatlashtirish → rahbar/ta'minotchiga xabar",
            "auto_reject": False,
        },
        {
            "id": "O2",
            "text": "Omborda muddati tugashiga 5 kun qolgan mahsulot katta partiyasini ko'rdingiz. Nima qilasiz?",
            "measures": "Proaktivlik, FIFO tushunchasi. To'g'ri: rahbarga xabar, zalga birinchi chiqarish, aksiya taklifi",
            "auto_reject": False,
        },
        {
            "id": "O3",
            "text": "Zaldan \"mahsulot tugadi, tez olib keling\" deyishdi, ayni paytda yangi mashina tushirilyapti. Qaysi birini qilasiz, nega?",
            "measures": "Ustuvorlik belgilash",
            "auto_reject": False,
        },
        {
            "id": "O4",
            "text": "Hamkasbingiz omborga begona odamni olib kirdi. Nima qilasiz?",
            "measures": "Xavfsizlik, qoidaga sodiqlik",
            "auto_reject": False,
        },
        {
            "id": "O5",
            "text": "Og'ir yuk tushirish paytida belingiz og'rib qoldi, smena tugashiga 3 soat bor. Nima qilasiz?",
            "measures": "Rostgo'ylik, o'zini asrash. \"Indamay ishlayveraman\" ham, \"tashlab ketaman\" ham past ball; to'g'ri: rahbarga aytish",
            "auto_reject": False,
        },
    ],
    "farrosh": [
        {
            "id": "F1",
            "text": "Zal o'rtasida mijoz shisha idishni tushirib yubordi, atrofda odam ko'p. Qadamma-qadam nima qilasiz?",
            "measures": "Xavfsizlik tushunchasi. To'g'ri: avval odamlarni ogohlantirish/to'sish, keyin tozalash",
            "auto_reject": False,
        },
        {
            "id": "F2",
            "text": "Siz endigina yuvgan joydan yana loy oyoq izlari qoldi. Ichingizda nima his qilasiz va nima qilasiz?",
            "measures": "Fe'l, sabr. Norozilik bildirish = qizil bayroq",
            "auto_reject": False,
        },
        {
            "id": "F3",
            "text": "Tozalash paytida javon ostidan pul (50 000 so'm) topib oldingiz. Nima qilasiz?",
            "measures": "Halollik. \"O'zimga olaman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "F4",
            "text": "Ish jadvalingizdagi hudud tugadi, smena tugashiga 1 soat bor. Nima qilasiz?",
            "measures": "Mehnatsevarlik, tashabbus",
            "auto_reject": False,
        },
        {
            "id": "F5",
            "text": "Mijoz sizdan \"guruch qayerda?\" deb so'radi. Javobingiz?",
            "measures": "Mijozga munosabat — farrosh ham do'kon yuzi. \"Bilmayman, men farroshman\" = past ball",
            "auto_reject": False,
        },
    ],
    "qoriqchi": [
        {
            "id": "G1",
            "text": "Chiqish eshigidagi signalizatsiya ishlab ketdi, mijoz \"men hech narsa olmadim\" deb ketishga urinmoqda. Aniq qadamma-qadam nima qilasiz?",
            "measures": "Protsedura bilishi, nizoni to'g'ri hal qilish. To'g'ri yo'nalish: xushmuomala to'xtatish, ayblamaslik, rahbarga xabar",
            "auto_reject": False,
        },
        {
            "id": "G2",
            "text": "Tungi smenada tanish do'stingiz \"faqat besh daqiqaga kirib chiqaman\" deb yopiq do'konga kiritishni so'ramoqda. Javobingiz?",
            "measures": "Halollik, qoidaga sodiqlik. Har qanday \"kiritib yuboraman\" = avtomatik rad",
            "auto_reject": True,
        },
        {
            "id": "G3",
            "text": "Hamkasbingiz omborda mahsulot o'g'irlayotganini ko'rdingiz. Nima qilasiz?",
            "measures": "Halollik. \"Hech nima qilmayman\" = avtomatik rad. To'g'ri: rahbarga xabar",
            "auto_reject": True,
        },
        {
            "id": "G4",
            "text": "Ikki mijoz o'rtasida janjal boshlanib, ovoz balandlashdi, atrofda bolalar bor. Qadamma-qadam nima qilasiz?",
            "measures": "Bosim ostida xotirjamlik, xavfsizlikni ta'minlash",
            "auto_reject": False,
        },
        {
            "id": "G5",
            "text": "Smena tugashiga 10 daqiqa qolganda yong'in signalizatsiyasi ishga tushdi. Nima qilasiz?",
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
