# EXE Creator

**Sayt havolasidan Windows uchun shaxsiy ikonka, to'liq ekran va ixtiyoriy chiqish paroliga ega o'rnatuvchi EXE yaratadigan Telegram bot.**

Bot sayt manzili, rasm, dastur nomi va parolni ketma-ket qabul qiladi. Python server C# va Microsoft WebView2 asosida Windows dasturini yig'adi, Inno Setup orqali o'rnatuvchi yaratadi va Telegramga yuboradi. Dastur ranglari saytning qora yoki oq mavzusiga avtomatik moslashadi.

**O'rnatuvchi versiyasi:** `1.2.1`  
**Platforma:** Windows 10/11 x64

> Muhim joriy holat: sertifikat sozlanmasa natija imzosiz yaratiladi. Ushbu loyihada Windows Application Control dastur EXE'sini `4551` xatosi bilan bloklagan. Imzolash integratsiyasi tayyor, ammo operatorning ishonchli code-signing sertifikatisiz ushbu kompyuterdagi blokni bartaraf etilgan deb hisoblash mumkin emas.

## Mundarija

1. [Loyiha haqida](#loyiha-haqida)
2. [Imkoniyatlar](#imkoniyatlar)
3. [Talablar](#talablar)
4. [Tez boshlash](#tez-boshlash)
5. [Muhit sozlamalari](#muhit-sozlamalari)
6. [Telegram orqali foydalanish](#telegram-orqali-foydalanish)
7. [Kiritish qoidalari](#kiritish-qoidalari)
8. [Windowsga o'rnatish](#windowsga-ornatish)
9. [To'liq ekran va chiqish](#toliq-ekran-va-chiqish)
10. [Avtomatik mavzu](#avtomatik-mavzu)
11. [4551 xatosi va imzolash](#4551-xatosi-va-imzolash)
12. [Telegramsiz EXE yaratish](#telegramsiz-exe-yaratish)
13. [Arxitektura va fayllar](#arxitektura-va-fayllar)
14. [Ma'lumotlar va parollar](#malumotlar-va-parollar)
15. [Testlar](#testlar)
16. [Xatolarni aniqlash](#xatolarni-aniqlash)
17. [Yangilash va xizmat](#yangilash-va-xizmat)
18. [Cheklovlar](#cheklovlar)
19. [Litsenziya va manbalar](#litsenziya-va-manbalar)

## Loyiha haqida

Loyiha ikkita alohida qismdan iborat:

- **Bot va yig'ish serveri:** Windows kompyuterida ishlaydi, so'rovlarni qabul qiladi va EXE yaratadi. Python, SDK va Inno Setup shu kompyuterga kerak.
- **Yaratilgan dastur:** foydalanuvchi kompyuteriga o'rnatiladi va saytni WebView2 ichida ochadi. Unda Python, Telegram yoki Inno Setup bo'lishi shart emas.

EXE saytning oflayn nusxasi emas. Unda sayt manzili va ilova sozlamalari joylanadi, sahifalar esa sayt serveridan yuklanadi. Saytga internet yoki ichki tarmoq orqali ulanish tayyor dastur ochilgan kompyuterdan ishlashi kerak.

## Imkoniyatlar

| Imkoniyat | Natija |
| --- | --- |
| Telegramdagi yaratish tugmasi | Savollar orqali bosqichma-bosqich EXE tayyorlash |
| HTTP/HTTPS havolalar | Protokol yozilmasa HTTPS qo'shish |
| Maxsus ikonka | EXE, Setup, oyna, Start va ish stoli yorlig'i uchun rasm |
| To'liq ekran | Ramka, sarlavha va kichraytirish/kattalashtirish tugmalarisiz oyna |
| Ixtiyoriy chiqish paroli | Chiqishdan oldin parol so'rash yoki parolsiz ishlash |
| Avtomatik mavzu | Sayt foniga mos panellar va parol dialogi |
| Navigatsiya | Orqaga, Bosh sahifa, Yangilash va Chiqish |
| O'rnatuvchi | Joriy Windows foydalanuvchisiga o'rnatish va uninstaller |
| Navbat | Bir vaqtda bitta yig'ish, foydalanuvchiga bitta faol ish |
| Ruxsatlar | Telegram ID bo'yicha ixtiyoriy cheklov |
| CLI | Tokensiz terminal orqali EXE yaratish |
| Imzolash | Sertifikat sozlansa dastur va Setup EXE'siga Authenticode imzosi |
| Natija nazorati | SHA-256 xeshi va BUILD-INFO.json |

## Talablar

### Bot va yig'ish kompyuteri

| Talab | Izoh |
| --- | --- |
| Windows 10/11 x64 | Yig'ish jarayoni Windows uchun yozilgan |
| Python 3.11+ | `python` buyrug'i terminalda ishlashi kerak |
| .NET Framework 4.8+ | Tizimdagi C# kompilyatori va WinForms |
| Windows PowerShell | Yuklangan vositalarning imzosini tekshirish |
| Internet | Telegram, paketlar va rasmiy vositalarni yuklash |
| BotFather tokeni | Faqat Telegram botni ishlatish uchun |
| Yozish huquqi | Loyiha, `.tools`, `work` va `dist` papkalariga |

Oddiy yig'ish uchun Visual Studio yoki zamonaviy .NET SDK kerak emas. `setup.bat` WebView2 SDK va Inno Setupni loyiha ichiga tayyorlaydi.

**Ixtiyoriy raqamli imzolash uchun:** ishonchli code-signing sertifikati, uning private key/token/HSM'iga kirish va Windows SDK tarkibidagi `signtool.exe`. Windows SDK Signing Tools avtomatik o'rnatilmaydi.

### Tayyor dastur ishlaydigan kompyuter

- Windows 10/11 x64.
- .NET Framework 4.8 yoki yangiroq.
- Microsoft Edge WebView2 Runtime.
- Sayt manziliga ulanish.
- Windows yoki tashkilotning Application Control siyosatiga muvofiqlik.

WebView2 Runtime bo'lmasa o'rnatuvchi Microsoft bootstrapperini ishga tushiradi; bunda internet kerak. .NET Framework 4.8 bo'lmasa talab ko'rsatiladi, u avtomatik yuklab o'rnatilmaydi.

## Tez boshlash

### 1. Loyiha papkasi

Ushbu kompyuterdagi manzil:

```text
C:\Users\User\Desktop\Project\exe Creator
```

```powershell
Set-Location -LiteralPath 'C:\Users\User\Desktop\Project\exe Creator'
python --version
```

Boshqa kompyuterda yo'lni loyiha joylashgan katalogga almashtiring.

### 2. Vositalarni tayyorlash

`setup.bat` ni ikki marta bosing yoki terminalda bajaring:

```powershell
.\setup.bat
```

Skript:

1. `.venv` virtual muhitini yaratadi.
2. `requirements.txt` paketlarini o'rnatadi.
3. Microsoft WebView2 SDK `1.0.4191.47` ni NuGet'dan oladi.
4. WebView2 Runtime bootstrapperini Microsoft'dan yuklaydi.
5. Inno Setup `6.7.3` ni `.tools\inno` ichiga o'rnatadi.
6. Microsoft va Inno Setup EXE yuklamalarining raqamli imzosini tekshiradi.
7. `--doctor` orqali yig'ish vositalarini tekshiradi.
8. `.env` yo'q bo'lsa `.env.example` dan nusxa yaratadi.

Mavjud `.env` almashtirilmaydi. Birinchi sozlashda internet zarur. Rasmiy vositaning imzosi tekshirilmasa sozlash muvaffaqiyatli yakunlanmaydi.

### 3. Tokenni sozlash

Telegramdagi **@BotFather** orqali bot yarating va tokenini `.env` fayliga yozing:

```dotenv
BOT_TOKEN=BOTFATHER_BERGAN_TOKENNI_SHU_YERGA_YOZING
ALLOWED_USER_IDS=
BUILD_COOLDOWN_SECONDS=60
MAX_PENDING_BUILDS=5
```

Token matni yuqorida faqat namuna. Haqiqiy tokenni README yoki kodga yozmang.

`.env` mavjud bo'lmasa xavfsiz nusxa olish:

```powershell
if (-not (Test-Path -LiteralPath '.env')) {
    Copy-Item -LiteralPath '.env.example' -Destination '.env'
}
```

### 4. Botni ishga tushirish

```powershell
.\start.bat
```

Yoki:

```powershell
.\.venv\Scripts\python.exe -m creator.bot
```

Telegramda `/start` yuboring. Bir token bilan **bitta faol bot nusxasi** ishlasin. Odatdagi konsol rejimini to'xtatish uchun **Ctrl+C** bosing.

Bot fonda alohida ishga tushirilgan bo'lsa, uning jarayoni alohida boshqariladi; `start.bat` mavjud fon nusxasini to'xtatmaydi. Kompyuter o'chsa, uyqu holatiga o'tsa yoki jarayon tugasa bot javob bermaydi. Windows service, autostart va avtomatik qayta ishga tushirish hozir sozlanmagan.

## Muhit sozlamalari

Sozlamalar `.env` dan olinadi. Tizimda belgilangan bir xil nomli muhit o'zgaruvchisi ustun turadi. O'zgarishdan so'ng botni qayta ishga tushiring.

| O'zgaruvchi | Standart | Vazifa |
| --- | --- | --- |
| `BOT_TOKEN` | Bo'sh | Telegram bot uchun majburiy token |
| `ALLOWED_USER_IDS` | Bo'sh | Vergul bilan ajratilgan ruxsatli Telegram IDlar |
| `BUILD_COOLDOWN_SECONDS` | `60` | Bir foydalanuvchining ish so'rovlari orasidagi vaqt |
| `MAX_PENDING_BUILDS` | `5` | Navbat, faol yig'ish va yuborilayotgan ishlarning umumiy chegarasi |
| `SIGN_CERT_SHA1` | Bo'sh | Sertifikatning 40 hex belgili thumbprint qiymati |
| `SIGN_CERT_STORE` | `CurrentUser` | `CurrentUser` yoki `LocalMachine`; store nomi `My` |
| `SIGNTOOL_PATH` | Bo'sh | SignTool yo'li; bo'sh bo'lsa PATH va Windows SDK'dan qidiriladi |
| `SIGN_TIMESTAMP_URL` | `http://timestamp.digicert.com` | RFC 3161 timestamp serveri |
| `REQUIRE_SIGNED_BUILDS` | `0` | `1` bo'lsa imzolash sozlanmaguncha bot/build ishlamaydi |

`ALLOWED_USER_IDS` bo'sh bo'lsa barcha **shaxsiy chatlarga** ruxsat beriladi. Guruhda EXE yaratish ishlamaydi. IDlarni olish uchun cheklovni yoqishdan oldin `/id` buyrug'idan foydalaning.

```dotenv
ALLOWED_USER_IDS=123456789,987654321
BUILD_COOLDOWN_SECONDS=120
MAX_PENDING_BUILDS=3
```

Kutish vaqti ish navbatga qabul qilingan paytdan hisoblanadi. Yig'ish xato tugasa ham avvalgi qabul vaqti hisobda qoladi. Kod kutish vaqtini kamida `0`, ishlar chegarasini kamida `1` deb oladi; son o'rniga noto'g'ri matn yozilsa sozlash xatosi chiqadi.

## Telegram orqali foydalanish

```text
/start → EXE yaratish
       → sayt havolasi
       → ikonka rasmi yoki Standart ikonka
       → dastur nomi
       → parol yoki Parolsiz davom etish
       → navbat va yig'ish
       → Nom-Setup.exe
```

| Buyruq | Vazifa |
| --- | --- |
| `/start` | Bosh menyu; tugallanmagan kiritishni tozalaydi |
| `/help` | Qisqa yordam |
| `/create` | Yangi EXE yaratishni boshlash |
| `/cancel` | Hali kiritilayotgan ma'lumotlarni bekor qilish |
| `/id` | Telegram user ID |

Yig'ish boshlanganidan keyin `/cancel` yoki `/start` uni to'xtatmaydi; natija chatga yuboriladi. Bir foydalanuvchining oldingi ishi tugamaguncha ikkinchi ish olinmaydi. Yig'ishlar bitta jarayon ichida ketma-ket bajariladi.

Suhbat holati operativ xotirada turadi. Oxirgi bosqich yangilanganidan 15 daqiqa o'tib keyingi kiritishda qayta boshlash so'raladi. Bot qayta ishga tushsa holatlar yo'qoladi. Bot o'chiq paytda yig'ilgan eski Telegram xabarlari ishga tushishda tashlab yuboriladi.

## Kiritish qoidalari

### Havola

- Faqat HTTP/HTTPS; protokol bo'lmasa HTTPS qo'shiladi.
- Eng ko'pi 2048 belgi; URL ichida bo'shliq va boshqaruv belgilariga ruxsat yo'q.
- `user:password@host` shaklidagi URL qabul qilinmaydi.
- `file://`, `javascript:` va boshqa tashqi protokollar rad etiladi.
- Domen, IPv4, IPv6, localhost va ichki tarmoq manzillari mumkin.

```text
example.com
https://example.com/app
http://192.168.1.10:8080/
http://[::1]:8080/
```

Bot saytning mavjudligini oldindan ochib tekshirmaydi. `localhost` tayyor dastur ochilgan kompyuterni bildiradi; bot serveridagi saytga avtomatik yo'naltirmaydi.

### Ikonka

| Parametr | Qiymat |
| --- | --- |
| Formatlar | PNG, JPG/JPEG, WEBP, BMP, ICO |
| Fayl hajmi | Ko'pi bilan 10 MiB: `10 × 1024 × 1024` bayt |
| Tasvir o'lchami | Ko'pi bilan 16 000 000 piksel |
| ICO freymlari | 16, 24, 32, 48, 64, 128, 256 px |

Foto yoki fayl sifatida yuborish mumkin. Shaffoflik va asl sifat uchun PNG ni **fayl sifatida** yuboring. Haqiqiy format dekoder bilan tekshiriladi; fayl kengaytmasini almashtirish yetarli emas.

Rasmning EXIF yo'nalishi hisobga olinadi, tomonlar nisbati saqlanib kvadrat maydonga joylashtiriladi. Rasm qirqilmaydi, chetda qolgan joy shaffof bo'ladi. Animatsiya saqlanmaydi: statik ikonka hosil qilinadi. Rasm kerak bo'lmasa **Standart ikonka** ni bosing.

### Dastur nomi

- 1–60 belgi; `.exe` qo'shimchasi ixtiyoriy va yozilsa olib tashlanadi.
- `CON`, `PRN`, `AUX`, `NUL`, `COM1`, `LPT1` kabi band nomlar mumkin emas.
- `< > : " / \ | ? * { }`, boshqaruv belgilari va oxirgi nuqta rad etiladi.

```text
Mening Saytim-Setup.exe   — tarqatiladigan o'rnatuvchi
Mening Saytim.exe         — o'rnatilgan dastur
```

### Chiqish paroli

4–128 Unicode belgi. Bo'shliqlar parolning bir qismi. Telegramda takroriy tasdiqlash bosqichi yo'q; parolni diqqat bilan kiriting. **Parolsiz davom etish** orqali uni tashlab ketish mumkin.

Terminaldagi `--ask-password` parolni ikki marta, ekranga ko'rsatmasdan so'raydi. Xato paroldan keyin dialogda qisqa kutish mavjud. Parolni tiklash xizmati yo'q. Bu saytga kirish paroli emas, faqat ilovadan chiqish uchun ishlatiladi.

## Windowsga ornatish

1. Telegramdan `Nom-Setup.exe` ni yuklang.
2. Windows xavfsizlik siyosati faylni ishga tushirishga ruxsat berishini tekshiring.
3. O'rnatuvchini oching.
4. Ish stoli yorlig'ini yaratish avvaldan belgilangan; xohlasangiz belgini olib tashlang.
5. O'rnatishni tugatib dasturni oching.

Standart katalog:

```text
%LOCALAPPDATA%\Programs\ExeCreator\<app-id>
```

Asosiy tarkib: `Nom.exe`, `Nom.exe.config`, `app.ico`, WebView2 Core/WinForms DLLlari, `WebView2Loader.dll`, `THIRD-PARTY-NOTICES.txt` va Inno Setup uninstaller fayllari.

Brauzer cookie/login seanslari alohida saqlanadi:

```text
%LOCALAPPDATA%\ExeCreator\<app-id>\BrowserData
```

Windowsdagi o'rnatilgan dasturlar ro'yxatidan olib tashlash mumkin. Brauzer profili avtomatik o'chirilmaydi. Uni qo'lda tozalashdan oldin dasturni yoping; saqlangan sayt sessiyalari ham yo'qoladi.

Bir xil **normallashtirilgan URL va nom** bir xil app-id beradi; qayta yaratilgan Setup avvalgi o'rnatishni yangilash uchun ishlatiladi. Mustaqil nusxa uchun boshqa nom tanlang. Yangilashdan oldin eski dasturni yoping: Setup uni majburan to'xtatmaydi.

## Toliq ekran va chiqish

Asosiy oyna kursor turgan monitorning to'liq o'lchamida ochiladi. Ramka, sarlavha, X va kichraytirish/kattalashtirish tugmalari bo'lmaydi. Oynaning tizimdagi ko'chirish, o'lcham, kichraytirish va restore buyruqlari rad etiladi. Ekran o'lchami o'zgarsa oyna moslashtiriladi.

| Tugma | Vazifa |
| --- | --- |
| Orqaga | Oldingi sahifa |
| Bosh sahifa | Boshlang'ich sayt manzili |
| Yangilash | Joriy sahifani qayta yuklash |
| Chiqish | Dasturni yopishni so'rash |

Parol bo'lsa **Chiqish**, **Alt+F4** va `window.close()` parol dialogini ochadi. To'g'ri parol yopadi; xato parol yoki bekor qilish saytga qaytaradi. Parol belgilanmasa to'g'ridan-to'g'ri yopiladi.

Bu ilova darajasidagi boshqaruv: Task Manager, administrator yoki Windows shutdown/restart'iga qarshi tizim qulfi emas. Brauzer ishga tusholmasa bo'sh oynada qolib ketmaslik uchun uni parolsiz yopish mumkin.

## Avtomatik mavzu

Sahifa yuklanganda va keyin taxminan har **800 ms** da ko'rinayotgan fon ranglari o'qiladi. Bir nechta nuqtadagi DOM/CSS fonlari, shaffof qatlamlar va `color-scheme` tekshiriladi. Navigatsiya, holat paneli va parol dialogi mos rangga, matn esa o'qiladigan qora yoki oq rangga o'tadi.

Saytning DOM yoki mavzu sozlamalari o'zgartirilmaydi. Saytda qora/oq rejim almashtirilsa qayta EXE yaratish kerak emas. Video, canvas, fon rasmlari, iframe va murakkab rangli dizaynlar qo'shimcha moslashtirish talab qilishi mumkin. Parol dialogining tizim sarlavha ranglari Windows DWM imkoniyatlariga bog'liq.

## 4551 xatosi va imzolash

```text
CreateProcess failed; code 4551.
An Application Control policy has blocked this file.
```

Bu xabar Windows siyosati EXE ishga tushishini rad etganini bildiradi. Kuzatilgan holatda Setup fayllarni joylashtirgandan keyin o'rnatilgan dastur EXE'sini ochishga uringanida blok yuz bergan. Bu xabar URL, ikonka yoki chiqish paroli noto'g'riligini anglatmaydi.

Smart App Control yangi yoki ishonchsiz faylni bloklashi mumkin. Ishonchli provayderning code-signing sertifikati bilan imzolash bo'yicha [Microsoft qo'llanmasi](https://learn.microsoft.com/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control)ga qarang. Tashkilotning alohida Application Control siyosati qo'shimcha nashriyot/ruxsat talablarini qo'yishi mumkin.

### Hozirgi holat

- Operatorning ishonchli signing sertifikati hali sozlanmagan.
- `SIGN_CERT_SHA1` bo'sh bo'lsa natija imzosiz bo'ladi; bot yuborish xabarida buni bildiradi.
- Integratsiya test dublari bilan tekshirilgan, haqiqiy sertifikat bilan ishlab chiqarish sinovi o'tkazilmagan.
- Ushbu Windows kompyuteridagi blok muammosi hali hal etilmagan.

Oddiy sayt SSL sertifikati code-signing sertifikati o'rnini bosmaydi. Self-signed sertifikat ommaviy tarqatishda ishonchli nashriyot sertifikati bilan teng emas.

### Sertifikat olingandan keyin

1. Provayder ko'rsatmasiga muvofiq sertifikat/private key yoki token/HSM'ni sozlang.
2. Windows SDK Signing Tools'ni o'rnating.
3. Bot ishlayotgan Windows foydalanuvchisi sertifikatdan foydalana olishini tekshiring.
4. `.env` dagi signing parametrlarini kiriting va botni qayta ishga tushiring.

Mavjud sertifikat metama'lumotlarini ko'rish:

```powershell
Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert |
    Select-Object Subject, Thumbprint, NotAfter, HasPrivateKey
```

Namunada joy tutuvchi matnlarni haqiqiy qiymatlarga almashtiring:

```dotenv
SIGN_CERT_SHA1=SERTIFIKATINGIZNING_40_HEX_BELGILI_THUMBPRINT_QIYMATI
SIGN_CERT_STORE=CurrentUser
SIGNTOOL_PATH=C:\Program Files (x86)\Windows Kits\10\bin\SDK_VERSIYASI\x64\signtool.exe
SIGN_TIMESTAMP_URL=http://timestamp.digicert.com
REQUIRE_SIGNED_BUILDS=1
```

`SIGN_CERT_SHA1` sertifikatni tanlash identifikatori; fayl imzosi algoritmi **SHA-256**. `SIGNTOOL_PATH` bo'sh bo'lsa vosita avtomatik qidiriladi.

```text
C# kompilyatsiyasi
  → dastur EXE'sini imzolash va tekshirish
  → Setup yaratish
  → Setup EXE'sini imzolash va tekshirish
  → yakuniy SHA-256
  → Telegramga yuborish
```

SignTool `My` store'dan sertifikatni tanlaydi, RFC 3161 timestamp oladi va `verify /pa /all /tw` bilan tekshiradi. Xato yoki warning natijasi muvaffaqiyat hisoblanmaydi. Imzolash so'ralganida kod imzosiz natijaga avtomatik o'tmaydi.

**Qamrov:** dastur va Setup EXE imzolanadi. Inno Setup yaratadigan uninstaller uchun alohida signing hook hozir sozlanmagan. Korporativ tarqatishda barcha bajariladigan komponentlarning siyosatga mosligini tekshiring. Mahalliy Authenticode tekshiruvi har qanday boshqa Windows siyosatida ruxsat kafolati emas.

Token/HSM PIN yoki interaktiv tasdiq talab qilsa, fon rejimida qo'shimcha sozlash kerak bo'lishi mumkin. Alohida bulutli signing xizmatining hisob/metadata integratsiyasi modulga kiritilmagan.

## Telegramsiz EXE yaratish

`setup.bat` bajarilgan bo'lsin. Telegram tokeni kerak emas; CLI ham `.env` signing sozlamalarini o'qiydi.

Muhitni tekshirish:

```powershell
.\.venv\Scripts\python.exe -m creator.builder --doctor
```

Parolsiz dastur:

```powershell
.\.venv\Scripts\python.exe -m creator.builder --url https://example.com --name "Mening Saytim" --no-password
```

Parol bilan:

```powershell
.\.venv\Scripts\python.exe -m creator.builder --url https://example.com --name "Mening Saytim" --ask-password
```

Maxsus ikonka bilan:

```powershell
.\.venv\Scripts\python.exe -m creator.builder --url https://example.com --name "Rasmli Sayt" --icon "C:\rasmlar\logo.png" --ask-password
```

`--ask-password` yoki `--no-password` dan bittasi majburiy. Parol buyruq qatoriga yozilmaydi; yashirin terminal so'roviga kiritiladi. `build-example.bat` namunaviy sayt uchun shu parolli rejimni ishga tushiradi.

## Arxitektura va fayllar

```text
exe Creator/
├── creator/
│   ├── bot.py                Telegram bosqichlari, ruxsat va navbat
│   ├── builder.py            Kompilyatsiya va paketlash
│   ├── config.py             Yo'llar va doimiy qiymatlar
│   ├── validation.py         URL, nom va parol xeshi
│   ├── icons.py              Rasm → ICO
│   ├── signing.py            Authenticode imzolash
│   └── tools_setup.py        Rasmiy vositalarni tayyorlash
├── windows/
│   ├── Program.cs            To'liq ekran va chiqish dialogi
│   ├── ExitProtection.cs     .NET parol tekshiruvi
│   ├── Theme.cs              Windows elementlarining ranglari
│   ├── theme.js              Sayt fonini o'qish
│   ├── installer.iss         Inno Setup shabloni
│   ├── app.manifest          Windows manifesti
│   └── App.config            .NET runtime talabi
├── tests/                    Python va native Windows tekshiruvlari
├── .env.example              Maxfiy qiymatlarsiz namuna
├── .gitignore
├── requirements.txt
├── setup.bat
├── start.bat
├── build-example.bat
├── README.md
├── .env                      Mahalliy token/sozlama
├── .venv/                    Python muhiti
├── .tools/                   SDK, bootstrapper, Inno Setup
├── work/                     Vaqtinchalik yig'ish/tekshiruvlar
├── dist/                     Tayyor natijalar
└── logs/                     Fonga yo'naltirilgan loglar
```

| Komponent | Belgilangan versiya |
| --- | --- |
| python-telegram-bot | `22.8` |
| python-dotenv | `1.2.1` |
| Pillow | `13.0.0` |
| Microsoft.Web.WebView2 | `1.0.4191.47` |
| Inno Setup | `6.7.3` |

Har bir ish uchun alohida tasodifiy job-id katalogi:

```text
dist/<job-id>/
├── Nom-Setup.exe
├── SHA256.txt
└── BUILD-INFO.json
```

`SHA256.txt` yakuniy, signing yoqilgan bo'lsa **imzolangandan keyingi** xeshni saqlaydi. `BUILD-INFO.json` versiya, fayl nomi, xesh va signing holatini qayd etadi. JSON mustaqil raqamli ishonch dalili emas; haqiqiy imzo Windows/SignTool bilan tekshiriladi.

Telegramga Setup EXE yuboriladi, yordamchi fayllar serverda qoladi. Xeshni tekshirish:

```powershell
Get-FileHash -LiteralPath 'C:\yol\Nom-Setup.exe' -Algorithm SHA256
```

Bot faylni yuborishdan oldin **49 000 000 bayt** chegarasini qo'llaydi. Katta natija diskda qolishi mumkin, ammo Telegramga yuborilmaydi.

## Malumotlar va parollar

- `.env` Gitga kiritilmaydi; token kod yoki README ichiga yozilmaydi.
- Xom chiqish paroli loyiha tomonidan diskka yoki EXE sozlamalariga yozilmaydi.
- 16 bayt salt, **PBKDF2-HMAC-SHA256, 210 000 iteratsiya, 32 bayt xesh** ishlatiladi.
- Telegramdagi parol xabarini bot imkon qadar darhol o'chiradi. Telegram va tizim xotirasida nusxalar qolmasligi kafolatlanmaydi.
- URL, nom va parol xeshi EXE resursiga kiritiladi; EXE tahliliga qarshi maxsus himoya yo'q.
- Cookie va sayt login seanslari mahalliy WebView2 profilida saqlanadi.
- WebView host obyektlari, WebMessage kanali, DevTools va odatdagi kontekst menyusi o'chirilgan.
- HTTP/HTTPS navigatsiyasida domen allowlist'i yo'q; sayt boshqa veb domenlarga o'tishi mumkin.

Sayt ruxsatlarini saytning o'zi boshqaradi. Chiqish paroli sayt hisobi yoki Windows administrator huquqlarining o'rnini bosmaydi.

## Testlar

To'liq to'plam:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Signing testlari:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*signing.py' -v
```

| Guruh | Qamrov |
| --- | --- |
| Validatsiya | URL/protokol/port, Windows nomlari, parol uzunligi va xeshi |
| Bot | Bosqichlar, rasm, limitlar, bekor qilish, ID ruxsatlari |
| Ikonka | ICO freymlari, shaffoflik, nisbat, format va o'lcham |
| Signing | Sozlama, SignTool argumentlari, tekshiruv, xato/warning va timeout |
| Yig'ish | Imzolashning paketlashdan oldin/keyin bajarilishi va xatoda to'xtash |
| Windows | To'liq ekran, tugmalarning yo'qligi, tizim buyruqlari, parol dialogi |
| WebView2 | Qora/oq mavzu, qayta yuklash va EXE/oyna ikonkalari |

Native testlar Windows yig'ish vositalari bo'lmasa o'tkazib yuboriladi. WebView2 testi mahalliy HTTP serverdan foydalanadi. Windows imzo siyosati test EXE'sini ham bloklashi mumkin.

**Tekshiruv chegarasi:** to'liq ekran o'zgarishidan keyin 20 ta test o'tgan. 1.2.1 o'zgarishlarida 29 ta Python testi qayta bajarilib muvaffaqiyatli o'tdi; o'zgarmagan native Windows testlari shu yangilashda takrorlanmadi. Signing oqimi haqiqiy sertifikatsiz test dublari yordamida tekshirilgan. Haqiqiy sertifikat, foydalanuvchi Application Control siyosati va imzolangan uninstaller uchun alohida qabul sinovi kerak.

## Xatolarni aniqlash

| Muammo | Tekshirish |
| --- | --- |
| `python` topilmadi | Python 3.11+ va PATH |
| `.venv` topilmadi | `setup.bat` ni bajaring |
| Token xatosi | `.env`, haqiqiy token va internet |
| `Conflict` | Shu token bilan ikkinchi bot nusxasi ishlamayaptimi? |
| Bot javob bermaydi | Jarayon, kompyuter holati, ID cheklovi va tarmoq |
| Guruhda ishlamaydi | Shaxsiy chatdan foydalaning |
| Holat eskirgan | `/create` bilan qayta boshlang |
| Navbat to'lgan | Ishlar tugashini kuting yoki limitni ko'rib chiqing |
| Rasm qabul qilinmadi | Format, 10 MiB / 16 MP chegarasi; PNG fayl yuboring |
| Nom rad etildi | Windows band nomlari va maxsus belgilar |
| Vosita yetishmaydi | `--doctor`, zarur bo'lsa `setup.bat` |
| Vosita imzosi tasdiqlanmadi | Rasmiy yuklama, tizim sanasi, sertifikat zanjiri va internet |
| `4551` | Application Control: signing/ruxsat talablari bajarilishi kerak |
| Sertifikat topilmadi | Thumbprint, scope, My store va private key huquqlari |
| Timestamp xatosi | Timestamp ulanishi va provayder holati |
| WebView2 ochilmadi | Runtime, .NET va profil papkasiga yozish huquqi |
| Sayt ochilmadi | Aynan EXE ishlayotgan kompyuterdan URL ga ulanish |
| OAuth/popup muammosi | Sayt oqimini joriy popup chekloviga moslashtirish |
| Fayl yuborilmadi | `dist`, fayl hajmi va Telegram ulanishi |
| Yangi funksiya yo'q | Yangi EXE yarating va eski nusxani yopib qayta o'rnating |

```powershell
.\.venv\Scripts\python.exe -m creator.builder --doctor
.\.venv\Scripts\python.exe -m pip check
```

`start.bat` odatda loglarni konsolga chiqaradi. Fon rejimi tashqi ishga tushirish buyrug'i orqali loglarga yo'naltirilgan bo'lsa, `logs\bot.stdout.log` va `logs\bot.stderr.log` ni tekshiring. Ichki log rotatsiyasi yoki monitoring xizmati mavjud emas.

## Yangilash va xizmat

1. Faol yig'ishlar tugashini kuting va mavjud bot nusxasini to'xtating.
2. Kodni yangilang; `.env` va kerakli natijalarni saqlang.
3. Bog'liqliklar o'zgargan bo'lsa ularni yangilang.
4. `--doctor` va tegishli testlarni bajaring.
5. Botning bitta nusxasini qayta ishga tushiring.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m creator.builder --doctor
```

Oldin tarqatilgan EXE avtomatik yangilanmaydi. Windows shabloni yoki EXE sozlamalari o'zgarsa yangi EXE yaratib tarqatish kerak.

`dist` natijalari avtomatik o'chirilmaydi. Odatdagi vaqtinchalik build kataloglari ish tugaganda tozalanadi; majburiy to'xtashdan qoldiqlar qolishi mumkin. `.tools` qayta ishlatiladi. `.venv` boshqa kompyuterga ko'chirilmaydi, o'sha kompyuterda qayta yaratiladi.

Manba kod va kerakli natijalarning zaxirasini saqlang. `.env` hamda sertifikat/private key zaxirasi faqat o'zingiz nazorat qiladigan joyda, provayder talablariga muvofiq saqlanadi. Loyiha private key'ni eksport qilmaydi.

## Cheklovlar

- Linux/macOS serveri va Windows x86/ARM64 uchun alohida native paketlar tayyorlanmagan.
- Saytning oflayn nusxasi, serveri yoki universal sayt konvertori yaratilmaydi.
- Yangi popup alohida oynada ochilmaydi; foydalanuvchi bosgan HTTP/HTTPS havola shu oynaga yo'naltiriladi. Ayrim OAuth oqimlari bunga mos kelmaydi.
- Mahalliy fayl va tashqi protokol navigatsiyasi bloklangan.
- Ma'lumotlar bazasi, admin paneli, ko'p serverli navbat va suhbat holatini tiklash yo'q.
- Avtomatik EXE yangilash va kod obfuskatsiyasi yo'q.
- Sertifikat xaridi, private key boshqaruvi va cloud signing hisobi integratsiyasi taqdim etilmagan.
- Standart natija imzosiz. Amaldagi Windows siyosatida alohida sinov zarur.
- To'liq ekran va chiqish paroli butun Windows tizimini qulflamaydi.

## Litsenziya va manbalar

Loyiha uchun alohida `LICENSE` fayli hali belgilanmagan. Uni avtomatik MIT yoki boshqa ochiq litsenziya deb hisoblamang; tarqatish shartlarini loyiha egasi alohida belgilaydi.

Uchinchi tomon komponentlari o'z litsenziyalariga ega. WebView2 litsenziya ma'lumotlari natijadagi `THIRD-PARTY-NOTICES.txt` ga qo'shiladi; bu loyiha uchun mustaqil litsenziya o'rnini bosmaydi.

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [python-telegram-bot hujjatlari](https://docs.python-telegram-bot.org/en/stable/)
- [WebView2 tarqatish tartibi](https://learn.microsoft.com/microsoft-edge/webview2/concepts/distribution)
- [WebView2 SDK paketi](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.4191.47)
- [Pillow ICO formati](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#ico)
- [Inno Setup](https://jrsoftware.org/isinfo.php)
- [.NET Framework 4.8](https://dotnet.microsoft.com/download/dotnet-framework/net48)
- [Windows SignTool](https://learn.microsoft.com/windows/win32/seccrypto/signtool)
- [Smart App Control uchun imzolash](https://learn.microsoft.com/windows/apps/develop/smart-app-control/code-signing-for-smart-app-control)
