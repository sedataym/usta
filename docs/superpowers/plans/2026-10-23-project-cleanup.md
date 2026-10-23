# USTA Proje Düzeni ve Uyumluluğu Koruma Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Bu belge uygulama yetkisi vermez; mevcut talep plan hazırlamaktır.

**Goal:** Mevcut özellikleri ve Linux/macOS uyumluluğunu koruyarak USTA'yı okunaklı, test edilebilir ve katkı verilmesi kolay bir açık kaynak projesine dönüştürmek.

**Architecture:** Mevcut Python/PySide6 uygulamasını küçük adımlarla düzenlemek. OCR, çeviri ve ekran yakalama modüllerini korumak; ana pencereden uygulama akışını ve dosya işlemlerini ayırmak. Yeni framework veya genel amaçlı eklenti sistemi eklememek.

**Tech Stack:** Python, PySide6, unittest, setuptools, mevcut OCR/çeviri sağlayıcıları, gettext, AppImage. Geliştirme araçları: Ruff, build ve kapsamı kademeli genişletilen mypy.

**Spec:** Kullanıcının 23 Ekim 2026 tarihli isteği: önceki incelemedeki tüm bulgular için plan; mevcut özellikler ve Linux/macOS uyumluluğu korunacak; temiz ve düzenli açık kaynak proje. Aşağıdaki kısıtlar bu isteğin uygulama önerisidir; henüz uygulanmamıştır.

## Global Constraints

- Linux KDE/GNOME ve macOS için mevcut başarılı kullanıcı akışları, arayüz yerleşimi, motor listeleri ve varsayılanlar korunacak.
- Linux'ta mevcut xcb varsayılanı ve kullanıcının QT_QPA_PLATFORM tercihi korunacak. Wayland/Portal/Spectacle yaklaşımı değiştirilmeyecek.
- macOS'ta native fullscreen Space, odak geri verme, overlay pencere seviyeleri, Cocoa bildirimleri ve ana thread üzerinde klavye düzeni okuma davranışı korunacak.
- Çoklu ekran, negatif ekran koordinatları, DPI kilidi/ölçekleme, bölge seçimini iptal etme ve geçici bölgenin 10 saniye sonra geri alınması korunacak.
- OCR motorlarının çalışma biçimi, metin temizleme kuralları, EasyOCR GPU/MPS tercihi ve Apple Vision dil/fallback davranışı korunacak.
- Google/DeepL dil kodları, API anahtarı kullanımı ve ayarların platforma özgü mevcut dizinleri korunacak.
- IPC socket adresi ve JSON alanları korunacak. Soket yolunu yeniden tasarlamak veya yeni bir single-instance mekanizması eklemek kapsam dışı.
- `usta`, `python run.py` ve AppImage başlatma akışları çalışmaya devam edecek. İç Python import yolları desteklenen dış API sayılmayacak.
- Eski ayar ve presetler kaybolmayacak. Geçiş geri alınabilir olacak; kaynak pickle dosyaları silinmeyecek veya üzerine yazılmayacak.
- Gerçekte çalışan Python/platform kombinasyonları önce kayda alınacak. `>=3.8` beyanı düzeltilirken destek daraltımı sessizce yapılmayacak; yeni bağımlılık sürümlerine toplu yükseltme yapılmayacak.
- Windows için yeni destek vaadi verilmeyecek; mevcut platform tanımları gereksiz yere silinmeyecek.
- Her aşama ayrı incelenebilir değişiklik olacak; yapısal taşıma ile çalışma davranışındaki hata düzeltmeleri ayrı commitlerde tutulacak.

## Review Focus

1. Çeviri sürerken motor/dil/bölge değişimi ve stop/start: eski sonuç yeni oturuma karışmayacak. Görev 7.
2. Kısmen bozuk/eski ayarlar ve yazma sırasında kesinti: özgün dosya korunacak, geçerli veri kurtarılacak. Görev 4.
3. macOS başka uygulamanın fullscreen Space'indeyken pencere açma/kapatma: Space ve odak korunacak. Görev 1, 8 ve 11.
4. Linux'ta Portal izninin iptali, eksik native bağımlılık ve yakalama sürerken kapatma: mevcut fallback korunacak, kaynaklar temizlenecek. Görev 1, 6 ve 11.
5. Kurulu wheel/AppImage'da kaynak ağacına erişim olmaması: ikonlar, çeviriler ve OCR modelleri bulunacak. Görev 2, 3 ve 11.

## Yaklaşım ve hedef yerleşim

Önerilen yaklaşım kademeli refaktör. Yalnız dosya adlarını düzeltmek sorumluluk ve thread sorunlarını çözmez; tek seferde yeniden yazmak platform regresyon riskini büyütür. Mevcut motorları ve native yardımcıları koruyarak modül sınırları adım adım kurulacak.

```text
src/usta/
  __init__.py                 # Hafif paket yüzeyi; GUI/native import yok
  __main__.py, main.py        # Giriş ve uygulama bileşenlerini bağlama
  config.py                  # Saf sabitler/varsayılanlar
  i18n.py
  application/
    settings.py              # Ayar/preset veri modelleri
    results.py               # OCR/çeviri sonuç ve hata modelleri
    controller.py            # UI ile worker arasında koordinasyon
    region_controller.py     # Ana/geçici bölge ve DPI durumu
    hotkey_controller.py     # Kısayol değiştirme/reset yaşam döngüsü
    pipeline.py              # UI'dan bağımsız OCR/çeviri iş akışı
    worker.py                # Qt thread/signal adaptörü
  core/
    ocr/                     # Mevcut motorlar ve registry
    translation/             # Mevcut motorlar ve registry
    screenshot/              # Mevcut native yakalama motorları
    platform/                # OS/DE tespiti, yetenekler, native hotkey
    shortcut.py, exceptions.py
  infrastructure/
    paths.py                 # Açıkça oluşturulan runtime yolları
    settings_store.py        # Atomik JSON yükleme/kaydetme
    legacy_settings.py       # Sınırlı ve tek seferlik eski dosya aktarımı
    socket_publisher.py      # Mevcut IPC sözleşmesi
    logging_setup.py
  ui/
    main_window.py, overlay_window.py
    tabs/                    # Kendi widget'larını yöneten sekme sınıfları
    region_selection/        # Eski core/sniper'ın görsel bölge seçimi
    platform/macos/          # Mevcut Cocoa pencere yardımcıları
    assets/
  resources/
    translations/
    ocr_models/rapidocr/
tests/
  unit/                      # OS/GUI/ağ gerektirmeyen testler
  integration/               # Qt ve bileşen bağlantıları
  native/                    # Gerçek desktop/macOS API testleri
  packaging/                 # Wheel/sdist kaynak ve kurulum testleri
  helpers/
docs/
  architecture.md
  development.md
  compatibility.md
  testing.md
```

Bu yapı görevler boyunca oluşacak; başlangıçta boş klasörler üretilmeyecek. `core` altında motorları korumak taşıma yükünü azaltır. Portal'ın 421 satır olması tek başına parçalama gerekçesi değildir; protokol ve kaynak yönetimi birlikte anlaşılabiliyorsa aynı modülde kalabilir.

## Görev 1 — Mevcut davranışı ve destek matrisini kayda al

**Dosyalar:** Mevcut `tests/test_*.py`; yeni `tests/unit/`, `tests/integration/`, `tests/native/`, `docs/compatibility.md`, `docs/testing.md`.

**Arayüz:** Mevcut public motor metotları, Qt sinyalleri ve kullanıcı eylemleri testlerin sınırıdır. Testler dosya uzunluğu veya özel alan adlarını doğrulamayacak.

- [ ] Mevcut 31 test metodunu sınıflandır; macOS sınıfı içinde kaldığı için Linux'ta atlanan Linux davranış testlerini platformdan bağımsız sınıflara taşı. Önce `python -m unittest discover -s tests -v` sonucunu ve skip nedenlerini kaydet.
- [ ] Varsayılanlar, motor listeleri, dil kodları, IPC alanları, OCR temizleme, ana/geçici bölge ve DPI davranışları için mevcut davranışı belgeleyen testler ekle. Bunların ilk etapta geçmesi beklenir; mevcut kusurlar ayrı regresyon testleriyle ilgili görevde ele alınır.
- [ ] Native testleri yalnız açık çalıştırma tercihiyle başlat; sıradan unit test komutu kullanıcı ekranını/kısayollarını kullanmasın. Atlanan native testleri başarılı platform doğrulaması olarak raporlama.
- [ ] Linux KDE Wayland+xcb, GNOME Wayland+xcb ve macOS native fullscreen için manuel senaryo listesi oluştur. OS/Python/Qt/CPU mimarisi ve native araç sürümlerini kaydet; erişilmeyen kombinasyonu doğrulanmadı olarak işaretle.
- [ ] `python -m unittest discover -s tests/unit -v` ve ilgili integration komutları geçsin; değişikliği ayrı committe kaydet.

## Görev 2 — Bağımlılık ve sürüm tanımlarını birleştir

**Dosyalar:** `pyproject.toml`, `requirements.txt`, `scripts/build-appimage.sh`; yeni `requirements-dev.txt`, `tests/packaging/test_metadata.py`.

**Arayüz:** `pip install .` mevcut varsayılan motorları ve kısayolları çalıştıracak; `pip install '.[paddle]'` isteğe bağlı Paddle desteğini kuracak. Geliştirme araçları `dev` extras grubunda olacak.

- [ ] Metadata testi yaz: DeepL/pynput runtime bağımlılıklarında bulunmalı; Paddle zorunlu olmamalı; iki kurulum yolunda Google Translate koşulu aynı olmalı. Mevcut çelişkilerde testin kaldığını doğrula.
- [ ] Çalışan ortamın sürümlerini kaydet. Python alt sınırını kod anotasyonları ve gerçekten kurulabilen bağımlılıklarla doğrula; 3.10+ başlangıç adayıdır, doğrulanmış destek matrisi kurulmadan kesin destek sözü verme. Alt sınır değişimi ve gerekçesini belgele.
- [ ] Temel bağımlılıkları `pyproject.toml` içinde tekilleştir. RapidOCR/Tesseract/EasyOCR varsayılan erişimini koru; Paddle'ı extras grubuna taşı. macOS PyObjC işaretlerini koru; platforma özel diğer bağımlılıkları import testleriyle ayır.
- [ ] `requirements.txt` dosyasını `.` üzerinden proje metadata'sını kullanan uyumluluk girişine dönüştür. AppImage scriptindeki requirements ve proje için tekrarlanan kurulumları tek kurulum akışında birleştir.
- [ ] Sürümü tek yerden üret; `APP_VERSION` erişimini koruyup AppImage scriptinin config dosyasını regex ile okumasını kaldır. Temiz ortamda metadata testleri ve `python -m pip check` geçsin; commit oluştur.

## Görev 3 — Gerçek paket adı ve dağıtım kaynakları

**Dosyalar:** `src/` → `src/usta/`; `run.py`, `pyproject.toml`, `babel.cfg`, `packaging/appimage/AppRun`, build scripti ve mevcut test importları. Yeni `src/usta/__main__.py`, `tests/packaging/test_artifacts.py`.

**Arayüz:** `usta`, `python -m usta`, `python run.py` aynı `usta.main:main()` fonksiyonuna ulaşacak. Kaynaklar `importlib.resources` ile çözülecek.

- [ ] Build artifact testi ekle: wheel/sdist içinde tüm mevcut ONNX dosyaları, ikonlar ve derlenmiş TR/UK katalogları bulunmalı. Repo dışından import edilebilmeli; yalnız editable kurulum yeterli sayılmamalı.
- [ ] Dosya taşımalarını ve import güncellemelerini birlikte yap; `sys.path` eklemesini kaldır. Bu committe algoritma/varsayılan değiştirme. Test patch hedeflerini ve helper scriptlerini güncelle.
- [ ] Modelleri ve çevirileri hedef resources dizinine taşı; runtime dosya yolu isteyen motorlara `importlib.resources.as_file()` ömrü doğru yönetilen kaynak ver. Model içeriklerinin hash'lerini koru.
- [ ] AppRun'u `python -m usta` ile başlat; ikon yollarını ve Babel katalog üretimini güncelle. `run.py` uyumluluk girişini koru.
- [ ] `python -m build`, artifact testleri ve temiz venv içine wheel kurulumu geçsin. Repo dışında başlatma ve native platform smoke testlerini kaydet; commit oluştur.

## Görev 4 — Doğrulanan modeller ve kayıpsız ayar/preset geçişi

**Dosyalar:** `ui/main_window.py`, `application/settings.py`, `infrastructure/settings_store.py`, `infrastructure/legacy_settings.py`; yeni `tests/unit/test_settings_store.py`, `tests/unit/test_settings_migration.py`.

**Arayüz:** `AppSettings` ve `Preset` dataclass'ları; `SettingsStore.load() -> AppSettings`, `save(settings: AppSettings) -> None`, `load_presets() -> dict[str, Preset]`, `save_presets(presets: dict[str, Preset]) -> None`. JSON şeması `schema_version=1` içerir.

- [ ] Mevcut ayar ve preset alanlarından anonim fixture oluştur. Renk/font, motor, dil, API anahtarı, kısayol, capture rectangle ve DPI değerlerinin aktarımda aynı kaldığını test et.
- [ ] Eksik alan, bilinmeyen alan/sürüm, bozuk dosya, yazma hatası, negatif ekran koordinatı ve yarım kalmış geçiş testlerini yaz. Başarısız yazmanın son geçerli dosyayı değiştirmediğini doğrula.
- [ ] Aynı dizinde geçici dosya + flush/fsync + `os.replace` ile JSON yaz. Alan doğrulaması geçerli eski değerleri keyfi aralıklara sıkıştırmasın. Gelecek şema sürümünü sessizce üzerine yazma.
- [ ] Yalnız mevcut yerel `settings.pkl`/`presets.pkl` dosyaları için primitive veri kabul eden, global/sınıf yüklemeyi reddeden sınırlı legacy okuyucu ekle. JSON başarıyla yazılıp tekrar okunmadan geçişi tamamlanmış sayma. Özgün pickle'ları koru; JSON varken eski pickle'ı yeniden çalıştırma.
- [ ] Yükleme sırasında `QSignalBlocker` kullan; yükleme sıfır kayıt tetiklesin, kullanıcı değişikliği tek tutarlı kayıt oluştursun. API anahtarları loga girmesin; yeni dosyalarda kullanıcıya özel izinler kullan. İlgili unit/integration testleri geçsin; commit oluştur.

## Görev 5 — Import yan etkileri, yollar ve loglama

**Dosyalar:** `config.py`, `main.py`, `core/platform/__init__.py`, `infrastructure/paths.py`, `infrastructure/logging_setup.py`, mevcut print kullanan modüller; yeni `tests/unit/test_bootstrap.py`.

**Arayüz:** `RuntimePaths` dataclass; `resolve_paths() -> RuntimePaths` yalnız hesaplar, `prepare_paths(paths: RuntimePaths) -> None` açıkça hazırlar. `configure_logging(level: str = "INFO") -> None` yalnız başlangıçta çağrılır.

- [ ] Paket/config importunun dizin oluşturmadığını, stdout'a yazmadığını ve platform dışı native bağımlılık yüklemediğini test et; mevcut yan etkiler nedeniyle ilgili testlerin kaldığını doğrula.
- [ ] Config'deki `makedirs` ve temp path printini bootstrap'a taşı; platform paketinin `__init__` yüzeyini hafiflet. Gerekli çalışma yollarını bileşenlere açıkça ver.
- [ ] `print()` çağrılarını anlamlı seviyelerle `logging` kullanımına çevir. Beklenmeyen hatalarda traceback, beklenen iptal/eksik bağımlılıkta kontrollü mesaj kullan; bütün genel catch bloklarını mekanik olarak kaldırma.
- [ ] API anahtarı, OCR metni ve tam ekran içeriğini varsayılan INFO loglarında yazma. UI metinlerinin ve başarılı sonuçların değişmediğini test et.
- [ ] `python -m unittest discover -s tests/unit -v` ve başlangıç integration testi geçsin; commit oluştur.

## Görev 6 — Motor kayıtları, sonuç sözleşmesi ve uyumluluk adaptörleri

**Dosyalar:** `core/ocr/ocr_manager.py`, `core/translation/translator_manager.py`, base sınıflar, motorlar/factory'ler; yeni `application/results.py`, `core/ocr/rapidocr_compat.py`, `tests/unit/test_engine_contracts.py`, `tests/unit/test_rapidocr_compat.py`.

**Arayüz:** `OCRResult(text: str, confidence: float | None = None)`, `TranslationRequest(text: str, source_lang: str, target_lang: str, engine_name: str, session_id: int)`, `TranslationResult(translated_text: str, source_lang: str, target_lang: str, engine_name: str, session_id: int)`, `EngineError(code: str, message: str)`. Sağlayıcı hatası `EngineError` üretir; UI bunu hata kanalında gösterir.

- [ ] Her mevcut motor için başarılı çıktı, boş OCR, dil kodu eşleme ve beklenen hata sözleşmesini fixture/fake ile test et. Hata metninin başarılı çeviri olarak yayınlanmaması için başarısız regresyon testi ekle.
- [ ] Kullanılmayan sonuç dataclass'larını tek sonuç modeline birleştir. Sağlayıcı hatalarını metin yerine tipli hataya çevir; kullanıcıya hata görünürlüğünü koru. UI ve worker tüketimini aynı görevde güncelle.
- [ ] UI listesi ve motor oluşturmayı ortak registry üzerinden bağla. Görünen adlar, sıralama ve varsayılanlar aynı kalsın; eksik bağımlılık yüzünden motorları sessizce listeden silme. Motorları ihtiyaç anında oluştur.
- [ ] RapidOCR thread sınırı uyarlamasını izole et; önce mevcut paketin public konfigürasyonuyla eşdeğer sonuç alınabildiğini test et. Alınamıyorsa sürüm kontrollü mevcut patch'i koru; private constructor ve pynput adaptörünü sözleşme testleriyle kapsa. GPU/MPS veya CPU thread değerlerini değiştirme.
- [ ] Ekran yakalama temel arayüzüne idempotent `close() -> None` ekle; `hasattr(close)` kontrollerini kaldır. Portal iptali ve mevcut fallback testleri geçsin; commit oluştur.

## Görev 7 — İş akışı, thread sahipliği ve kontrollü kapanış

**Dosyalar:** `core/worker.py` → `application/worker.py`; yeni `application/pipeline.py`, `tests/unit/test_pipeline_lifecycle.py`, `tests/integration/test_worker_signals.py`; ilgili UI bağlantıları.

**Arayüz:** `Pipeline.configure(settings: AppSettings) -> None`, `start() -> None`, `stop() -> None`; Qt adaptöründe mevcut `new_translation`, `performance_update`, `translation_status`, `running_status` sinyalleri korunur; hata için ayrı `error_occurred(str)` sinyali eklenir.

- [ ] Fake capture/OCR/translator ile bloke API çağrısı, stop sırasında sonuç, ardışık stop/start, dil/motor/bölge değişimi ve capture hatası senaryolarını test et. Gerçek ağ, rastgele sleep veya OCR modeli gerektirmesin; Event/barrier kullan.
- [ ] Her işin settings/motor/dil/region snapshot'ını oluştur. Tek sahipli komut kuyruğu üzerinden yapılandır; worker'ın kullandığı motoru GUI thread'inde kapatma/değiştirme. Ağ çağrısı boyunca global lock tutma.
- [ ] Tek aktif çeviri yürütücüsünü açıkça sahiplen; takip edilmeyen daemon thread kaldır. Her stop/config değişiminde session kimliğiyle eski sonucu ele. İptal edilemeyen çağrı yeni oturuma sonuç gönderemesin.
- [ ] Yakalama/sağlayıcı beklemelerine sonlu timeout koy; stop isteği GUI event loop'unu bloklamasın. Kaynaklar kendi thread'inde temizlensin; Qt worker tamamlanmadan nesnesi yok edilmesin. Sahte sağlayıcılarla zaman sınırını doğrula; gerçek ortam değerlerini uyumluluk kaydına yaz.
- [ ] Başlat/durdur tekrarı, hata/boş metin, yinelenen metin bastırma, 0.2 saniyelik döngü aralığı ve IPC metadata doğruluğu testleri geçsin. Önceki/sonraki performansı aynı fixture ve donanımda karşılaştır; commit oluştur.

## Görev 8 — Ana pencere, sekmeler ve bölge seçimi sınırları

**Dosyalar:** `ui/main_window.py`, `ui/tabs/*.py`, `application/controller.py`, `application/region_controller.py`, `application/hotkey_controller.py`; `core/sniper/` → `ui/region_selection/`; `ui/macos_*.py` → `ui/platform/macos/`; yeni `tests/integration/test_control_panel.py`.

**Arayüz:** Sekmeler `set_settings(settings: AppSettings) -> None` ve alanlara özgü Qt sinyalleri sunar; `ControlPanel` widget'ları oluşturup signal bağlar. `RegionController.apply_main_region(rect: QRect, dpi_scale: float | None = None)`, `apply_temporary_region(rect: QRect, dpi_scale: float | None = None)`, `restore_main_region()` bölge durumunun tek sahibidir.

- [ ] Kullanıcı eylemiyle ayar değişimi, preset uygulama, kısayol değişimini reddetme/eski kısayolu koruma ve 10 saniyelik bölge geri dönüş testlerini ekle. Aktif geçici bölge sırasında preset yüklenince eski bölgeye yanlış geri dönmeme regresyonunu kapsa.
- [ ] Dosya işlemlerini store'a, worker koordinasyonunu controller'a, hotkey yaşam döngüsünü hotkey controller'a taşı. Ana pencere ve sekmeler worker alanlarına doğrudan yazmasın.
- [ ] Sekmeleri kendi widget'larını yöneten sınıflara dönüştür. Ortak font/renk uygulamasını tek metotta topla; UI sırası, metinleri, kısayollar ve görünümü korunacak. Dosya satır sayısını yapay hedef yapma.
- [ ] Region selector widget'larını UI katmanına taşı. Qt dışı motor modüllerinin `usta.ui` import etmediğini mimari testle doğrula. Native pencere bayraklarını, Cocoa çağrı sırasını ve GUI thread üzerinde deleteLater davranışını değiştirme.
- [ ] GUI thread'indeki `time.sleep(0.2)` yerine aynı seçim öncesi gecikmeyi `QTimer` ile sağla. İptal/başarılı seçim, iki platform pencere davranışı ve tüm mevcut native testler geçsin; commit oluştur.

## Görev 9 — IPC ve geçici dosya kaynak yönetimi

**Dosyalar:** `core/socket_publisher.py` → `infrastructure/socket_publisher.py`, `infrastructure/paths.py`, yakalama yollarını kullanan motorlar; yeni `tests/unit/test_socket_publisher.py`, `tests/unit/test_runtime_paths.py`.

**Arayüz:** `TranslationPublisher` mevcut JSON broadcast parametrelerini ve socket yolunu korur. `RuntimePaths` her uygulama oturumu için özel capture dizini taşır; IPC yolu ayrı kalır.

- [ ] İki istemci, bağlantı kopması, okumayan istemci, stop/start ve aynı adresin başka aktif süreç tarafından kullanılması testlerini yaz. Yavaş bir istemci diğer yayınları ve kapanışı sınırsız süre bloke etmesin.
- [ ] Socket gönderimini sınırlı bekleme/kuyrukla yönet; taşan/yavaş bağlantıyı kontrollü kapat. Çalışan başka sürecin socket dosyasını stale sanıp unlink etme; kullanımda adres için anlaşılır hata üret. Yeni IPC protokolü ekleme.
- [ ] Capture dosyalarını oturuma özel temp dizinine taşı; Linux'ta mevcut `/dev/shm` tercihini ve macOS'ta temp fallback'ini koru. Başarı/hata/kapanışta yalnız kendi dosyalarını temizle.
- [ ] `python -m unittest tests.unit.test_socket_publisher tests.unit.test_runtime_paths -v` geçsin. IPC JSON fixture'ı alan ve tür düzeyinde aynı olsun; commit oluştur.

## Görev 10 — Okunabilirlik ve katkı standartları

**Dosyalar:** `pyproject.toml`, `.gitignore`, `README.md`; yeni `CONTRIBUTING.md`, `docs/architecture.md`, `docs/development.md`, `docs/compatibility.md`, `CHANGELOG.md`, `.github/ISSUE_TEMPLATE/bug_report.yml`, `.github/pull_request_template.md`.

**Arayüz:** `ruff check .`, `ruff format --check .`; mypy başlangıçta saf application veri modelleri ve infrastructure store modüllerini kapsar. Native SDK'lar için geniş kapsamlı `ignore_errors` kullanılmaz.

- [ ] Ruff ile import/unused ve biçim kurallarını tekilleştir; mekanik biçim değişikliklerini işlevsel değişikliklerden ayrı committe tut. Qt override adlarını koru; yeni uygulama metotlarında snake_case kullan.
- [ ] Eski yorumları ve gerçekten kullanılmayan importları kaldır; çalışır alternatif backend'leri sırf o an kullanılmıyor diye silme. Türkçe/Ukraynaca kataloglar ve msgid'ler korunacak; mevcut çevrilmemiş UI metinlerini ayrı katalog güncellemesiyle kapsa.
- [ ] README'de mevcut macOS desteği ile eskimiş roadmap'i uzlaştır; kurulum, çalıştırma, sistem bağımlılıkları, Paddle extras, AppImage ve test komutlarını açıkla. Belgeleri repo'nun mevcut İngilizce diliyle tutarlı yaz.
- [ ] CONTRIBUTING'e geliştirme kurulumu, mimari sınırlar, format/test komutları ve native test gereksinimlerini ekle. Bug şablonunda OS/DE/session/Python/Qt/motor bilgilerini iste; anahtar/ekran metni paylaşılmamasını belirt.
- [ ] `.venv/`, araç cache'leri ve yerel çıktılar ignore edilsin. Lisansı koru; model dosyalarının kaynak/lisans bilgilerini mevcut kanıtlardan belgeleyip doğrulanamayanları açıkça işaretle. Araç kontrolleri geçsin; commit oluştur.

## Görev 11 — CI, dağıtım ve gerçek platform kabulü

**Dosyalar:** yeni `.github/workflows/ci.yml`, `.github/workflows/package.yml`, `tests/packaging/`; `docs/testing.md`, `docs/compatibility.md`, `docs/appimage.md`.

**Arayüz:** PR kontrolleri format/lint, saf testler, Qt integration testleri ve artifact doğrulamasıdır. Gerçek masaüstü/native test sonuçları bunlardan ayrı raporlanır.

- [ ] Linux ve macOS runner'larında Görev 2'de doğrulanmış Python sürümleriyle CI matrisi kur. Ağ/model indiren OCR ve gerçek sağlayıcı çağrılarını unit testlerden ayır. Testlerdeki skip sayısını ve nedenlerini görünür tut.
- [ ] Yeni modeller/store/pipeline için mypy, wheel/sdist build ve temiz venv kurulum kontrolünü ekle. Önceki 10-test örneklemini tüm testler geçmiş gibi sunma; her test grubunun sonucu ayrı kaydedilsin.
- [ ] Linux Qt integration testlerini sanal ekranla çalıştır. Sanal ekranın gerçek Wayland/Portal davranışını kanıtlamadığını belgeleyip KDE ve GNOME masaüstünde manuel kabulü ayrı çalıştır.
- [ ] macOS'ta izinler, fullscreen Space, çoklu ekran/Retina, kısayol tekrar bağlama, odak iadesi ve Apple Vision native testlerini gerçek oturumda çalıştır. Desteklenen mimarilerden erişilemeyenleri doğrulanmadı olarak işaretle.
- [ ] AppImage'i gerçek Linux masaüstünde çalıştır: ikon/katalog/modeller, Portal iptali, Spectacle, ayar geçişi ve IPC kontrolü. Kaynak kurulum ve kurulu wheel için aynı kullanıcı senaryolarını doğrula.
- [ ] Aynı OCR fixture/donanımda süre, bellek ve kapanış gecikmesini başlangıç kaydıyla karşılaştır; ölçüm gürültüsünü aşan kötüleşmeleri araştır. Belgelenmemiş platform regresyonu varsa ilgili aşamayı geri al; yayınlamadan önce düzelt.

## Bulguların görevlerle eşlemesi

| İnceleme bulgusu | Görev |
|---|---|
| Bağımlılık kaynaklarının çelişmesi | 2 |
| Python alt sürüm beyanının yanlışlığı | 1, 2, 11 |
| Ana pencerenin fazla sorumluluğu | 4, 7, 8 |
| Worker paylaşılmış durum/kapanış sorunu | 7 |
| Sekmelerin panel alanlarına bağımlılığı | 8 |
| Ayar yüklerken kayıt, pickle/atomik yazım | 4 |
| Core → UI bağımlılığı | 8 |
| Hatanın normal çeviri metni sayılması | 6, 7 |
| Paket adı, sys.path ve model paketleme | 3 |
| Print/genel exception, RapidOCR patch | 5, 6 |
| Test dağılımı, CI/lint/type check eksikliği | 1, 10, 11 |
| IPC bloklama ve ortak geçici dosyalar | 9 |

## Uygulama sırası ve geri dönüş

Sıra: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11**. Bir sonraki görev başlamadan önce önceki görevin kontrolleri geçmeli; native yapıyı etkileyen görevler için ilgili platform kontrolü de gerekli. Görev 11'de CI'ye taşınacak kontroller görevler sırasında yerelde çalıştırılır.

Her görev ayrı review/commit sınırıdır; gerekirse içindeki mekanik ve davranış değişiklikleri ayrı commitlere bölünür. Uygulama başında mevcut çalışma ağacındaki kullanıcı değişiklikleri korunur. Ayar geçişinde eski pickle dosyaları durduğu için kod geri alındığında eski sürüm kendi dosyalarını okuyabilir; yeni sürümde yapılan JSON değişikliklerinin eski sürüme otomatik aktarılmadığı belgelenir.

## Tamamlanma koşulları

- [ ] Tüm bulguların karşılığında uygulanmış değişiklik veya kanıtlı, açık gerekçeli karar var.
- [ ] Linux KDE/GNOME ve macOS başarılı kullanıcı senaryoları başlangıç kaydıyla aynı; doğrulanmamış platform sonucu başarılı gösterilmiyor.
- [ ] Eski ayar/presetler korunarak yükleniyor; durdurulan/eski iş overlay veya IPC'ye sonuç gönderemiyor.
- [ ] Ana pencere dosya işlemi yapmıyor; sekmeler worker'a doğrudan erişmiyor; core motorlarından UI'a import yok.
- [ ] Wheel/sdist/AppImage kaynakları eksiksiz; temiz ortamda başlatma yolları çalışıyor.
- [ ] Testler, lint/format, tanımlı tip kontrolleri ve paket testleri geçiyor; native kabul kaydı mevcut.
- [ ] README/katkı/mimari/test belgeleri gerçek komutlarla uyumlu; yeni geliştirici temiz clone üzerinden kurulumu tekrarlayabiliyor.

## Plan öz denetimi

Bu plan önceki incelemedeki 11 maddeyi ve inceleme sırasında görülen IPC/geçici dosya risklerini görevlerle eşleştirir. Mevcut davranışı kayda alma testleri başta; bilinen kusurların başarısız regresyon testleri ilgili düzeltme görevindedir. Dış sağlayıcı sözleşmesini değiştiren bir API geliştirme işi planlanmaz; mevcut istemciler korunur. Plan hazırlama aşamasında uygulama kodu, bağımlılıklar ve platform ayarları değiştirilmez.
