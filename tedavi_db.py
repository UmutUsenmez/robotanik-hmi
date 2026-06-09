# tedavi_db.py

DISEASE_DATABASE = {
    "Mosaic Virus": {
        "T1": "Vektor bocek (yaprak biti) tespiti icin sari yapiskan tuzaklar as. Hastalik suphesi olan bitkiyi dijital haritada isaretle ve gozlem sikligini artir.",
        "T2": "Vektor bocekleri uzaklastirmak icin Neem (Nim) yagi uygula. Cevredeki yabani otlari (viruslerin dogal deposu) mekanik olarak temizle.",
        "T3": "Virusun tedavisi yoktur! Enfekte bitkileri kokunden sok, kapali plastik posetlere koyarak tarladan derhal uzaklastir ve yak (Roguing). Kalan saglikli bitkilere vektor bocekler icin acil sistemik insektisit at."
    },
    "Yellow Leaf Curl Virus": {
        "T1": "Beyaz sinek hareketliligini izle. Seranin havalandirma tullerini kontrol et ve delikleri fiziksel olarak onar.",
        "T2": "Beyaz sinek populasyonunu baskilamak icin organik potasyum sabunu puskurt. Sera icine avci/yirtici bocek salinimi planla.",
        "T3": "Sokum ve imha zorunludur! Hastalikli bolgeyi fiziksel olarak izole et. Yayilimi durdurmak icin saglam bitkilere beyaz sineklere karsi direnc kirici kimyasal insektisit pompala."
    },
    "Late Blight": {
        "T1": "Yaprak islaklik suresini acilen dusur. Yagmurlama sulamayi derhal durdur, tamamen damlama sulamaya gec. Seradaki fanlari maksimum kapasiteye al.",
        "T2": "Hastaligi yavaslatmak ve saglikli dokulari korumak icin organik bakir sulfat (bordo bulamaci) uygula.",
        "T3": "Agresif salgin tehlikesi! Hizli etkili, spor oldurucu sistemik fungisit (orn: Curzate) ile tum bolgeyi acil ilacla. Kurtarilamayacak curuk dallari kes ve imha et."
    },
    "Bacterial Spot": {
        "T1": "Sabah erken saatlerde veya gece sulama yapmayi birak. Yapraklarin uzerinde su damlasi kalmasini engelle.",
        "T2": "Toprak yuzeyini kalin bir saman malc (mulch) ile kapatarak topraktaki bakterilerin yapraga sicramasini fiziksel olarak onle. Bitki bagisiklik guclendiriciler kullan.",
        "T3": "Bakir ve Mancozeb karisimi ile kimyasal tedavi uygula. Enfekte olmus meyveleri sterilize edilmis aletlerle keserek uzaklastir."
    },
    "Early Blight": {
        "T1": "Hastalik ilk alt yapraklarda baslar. Tabandaki yasli, topraga degen ve sararmis yapraklari budayarak taban havalandirmasini artir.",
        "T2": "Toprak koklerine aktif 'Kompost Cayi' dokerek topraktaki faydali mikrobiyolojiyi canlandir (faydali mikroplarin patojenle rekabet etmesini sagla). Hafif organik fungisit at.",
        "T3": "Hastalik ust dallara sicradi. Genis spektrumlu sistemik mantar ilaci pompalamasi baslat."
    },
    "Spider Mites": {
        "T1": "Tozlanmayi engellemek icin yuruyus yollarini islat. Orumcekler nemi sevmedigi icin yapraklara hafif su sisi (misting) ver.",
        "T2": "Tarlaya Phytoseiulus persimilis (avci kirmizi orumcek) gibi predator bocekler salarak populasyonu biyolojik olarak bitir. Organik sabunlu su sik.",
        "T3": "Hem yetiskinleri hem de larvalari ayni anda yok eden spesifik kimyasal akarisit (miticide) ile yogun ilaclama yap."
    },
    "Septoria": {
        "T1": "Kok bogazinin hava almasi icin alt 30 cm'lik kisimdaki yapraklari kesip seradan cikar. Bitki araliklarini ac.",
        "T2": "Hastalikli bolgedeki topraga seffaf naylon sererek 'Solarizasyon' (gunes isisiyla firinlama) yap ve kislayan mantar sporlarini etkisiz hale getir.",
        "T3": "Hastalik tehlikeli tirmanisa gectiyse Chlorothalonil bazli fungisit ile genel kimyasal ilaclama dongusu baslat."
    },
    "Leaf Mold": {
        "T1": "Nemin %85'i gectigi alanlar. Sera pencerelerini tam ac, havalandirma suresini uzat. Sik yaprakli dallari seyrelt.",
        "T2": "Gece-gunduz sicaklik farkindan dogan ciglenmeyi (dew point) kirmak icin otonom isiticilari devreye sokarak ortami fiziksel olarak kurut. Organik kukurt at.",
        "T3": "Fiziksel kurutmaya ragmen devam eden inatci enfeksiyon durumu. Nufuz edici sistemik mantar ilaci uygula."
    },
    "Leaf Miner": {
        "T1": "Hasar cogunlukla kozmetiktir. Uzerinde tunel izleri olan yapraklari kopar ve larvalari oldurmek icin fiziksel olarak ez.",
        "T2": "Ortama Diglyphus isaea isimli asalak yabanarilarini sal. Arilar dogrudan yapragin icine girip larvalari bulup yok edecektir. Yapraklara mineral yag puskurt.",
        "T3": "Yaprak alaninin buyuk kismi yok olduysa, Spinosad bazli veya yaprak dokusuna isleyen (translaminar) bocek ilaci ile bolgesel kimyasal mudahale yap."
    }
}

def get_treatment(disease_name, danger_percent):
    """Hastalık adını ve yüzdeyi alıp ilgili tedavi önerisini döndürür."""
    # Yüzdeye göre risk seviyesi belirleme
    if danger_percent < 50:
        risk_level = "T1"
        risk_text = "Dusuk Risk"
    elif danger_percent < 75:
        risk_level = "T2"
        risk_text = "Orta Risk"
    else:
        risk_level = "T3"
        risk_text = "Yuksek Risk"

    # Veritabanında eşleşme arama (Kısmi isim eşleşmelerini de yakalar)
    for db_disease, treatments in DISEASE_DATABASE.items():
        if db_disease.lower() in disease_name.lower() or disease_name.lower() in db_disease.lower():
            return f"[{risk_text}] Oneri: {treatments[risk_level]}"
            
    # Eğer hastalık veritabanında yoksa genel bir mesaj döndür
    return f"[{risk_text}] Oneri: Spesifik tedavi kaydi bulunamadi. Uzman kontrolu onerilir."