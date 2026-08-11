# EventFlow Decisions

Bu belge değişen mimari ve iş kurallarının aktif karar kaydıdır. “Kabul edildi” kararı, ilgili davranışın mevcut PR'da tamamlandığı anlamına gelmez; uygulama PR'ı ayrıca belirtilir. Bir karar değişirse alternatifleri ve bedeliyle birlikte bu belge ve ilgili testler aynı PR'da güncellenir.

## D-001 — FastAPI modüler monolit

Durum: Kabul edildi; foundation PR 1'de uygulanıyor, domain use-case'leri PR 2-4'te tamamlanacak.

Karar: Backend tek deploy edilebilir FastAPI uygulaması olacak; `auth`, `users`, `events`, `reservations`, `idempotency`, `audit` ve ortak altyapı ayrı modül sınırlarında tutulacak.

Değerlendirdiğim alternatifler: Başlangıçtan mikroservisler; katmansız tek paket; Django monolit.

Neden bunu seçtim: Domain transaction'ları aynı PostgreSQL sınırında atomik kalırken modül sahipliği görünür olur. Küçük ekip için network, service discovery ve dağıtık transaction maliyeti oluşmaz.

Neyi feda ettim: Modüller bağımsız deploy ve ölçeklenemez; sınırlar kod review ve import disipliniyle korunur.

## D-002 — PostgreSQL ve async SQLAlchemy

Durum: Kabul edildi ve PR 1'de uygulandı.

Karar: Domain verisinin kaynağı PostgreSQL; uygulama erişimi async SQLAlchemy/asyncpg, şema yönetimi yalnız Alembic olacaktır.

Değerlendirdiğim alternatifler: SQLite, sync ORM, MongoDB, runtime `create_all`.

Neden bunu seçtim: Row lock, unique-conflict, partial index, JSONB, trigger ve transaction davranışları kapasite/idempotency/audit kurallarını doğrudan destekler. Async erişim FastAPI request modeline uyar.

Neyi feda ettim: Lokal geliştirme için gerçek PostgreSQL gerekir; async transaction testleri ve migration disiplini daha fazla kurulum maliyeti taşır.

## D-003 — Event row lock ve `reserved_count`

Durum: Şema PR 1'de; event-first create/reactivate/cancel writer'ları PR 4'te uygulandı, 200 istek kapasite kanıtı PR 4 kapanış kapısında çalıştırılacak.

Karar: Rezervasyon writer'ları event satırını `FOR UPDATE` ile serialization point yapacak; kapasite `events.reserved_count` üzerinden aynı transaction'da güncellenecek.

Değerlendirdiğim alternatifler: Her istekte reservation `COUNT(*)`; yalnız optimistic retry; Redis counter; distributed lock.

Neden bunu seçtim: Tek authoritative transaction içinde kapasite kontrolü ve sayaç güncellemesi yapılır; database constraint de `0 <= reserved_count <= capacity` invariant'ını korur.

Neyi feda ettim: Popüler tek event satırında write contention oluşur; çok büyük ölçekte queue/waiting-room gerekebilir.

## D-004 — Idempotency tablosu ve doğal unique anahtar

Durum: Şema PR 1'de; atomik owner/conflict/replay algoritması ve rollback takeover testi PR 4'te uygulandı.

Karar: Idempotency sahipliği `(user_id, operation, key)` unique constraint'iyle PostgreSQL'de claim edilecek; request hash, state ve semantic response snapshot aynı transaction sınırında tutulacak.

Değerlendirdiğim alternatifler: Redis lock/cache; process memory; yalnız reservation unique constraint; client-side retry suppression.

Neden bunu seçtim: Concurrent insert unique-conflict'i bütün backend replica'ları için tek sahip seçer ve domain commit'iyle replay snapshot'ı atomik kalır.

Neyi feda ettim: Her idempotent işlem ek satır/index write'ı ve retention cleanup gerektirir; loser istek unique-conflict sonrası transaction sınırını doğru yönetmelidir.

## D-005 — UTC instant ve IANA timezone

Durum: Server validation PR 3'te uygulandı ve DST/offset testleriyle kanıtlandı; UI doğrulaması PR 5'te.

Karar: Etkinlik zamanı PostgreSQL `timestamptz` ile UTC instant olarak, kullanıcı bağlamı ayrıca IANA timezone adıyla saklanacak.

Değerlendirdiğim alternatifler: Naive local datetime; yalnız UTC; sabit numeric offset.

Neden bunu seçtim: UTC sıralama/karşılaştırmayı kararlı yapar; IANA zone gelecekteki gösterim ve DST kural bağlamını korur.

Neyi feda ettim: API create/PATCH daha katı offset-zone doğrulaması ve timezone veri tabanı bağımlılığı taşır.

## D-006 — Version ile optimistic concurrency

Durum: API conflict akışı PR 3'te gerçek eşzamanlı PostgreSQL testiyle uygulandı; UI conflict akışı PR 5'te.

Karar: Event update, client'ın gördüğü `version` ile koşullu yapılacak; stale update deterministik `409 EVENT_VERSION_CONFLICT` üretecek.

Değerlendirdiğim alternatifler: Last-write-wins; bütün edit boyunca pessimistic lock; ETag olmadan timestamp karşılaştırması.

Neden bunu seçtim: Uzun kullanıcı edit süresince DB lock tutulmadan kayıp update görünür hale gelir.

Neyi feda ettim: Client conflict'i kullanıcıya göstermeli ve güncel veriyi yeniden yükleme/uzlaştırma akışı sunmalıdır.

## D-007 — Soft event cancellation

Durum: Event soft-cancel ve kilit sırası PR 3'te; aktif reservation bulk transition'ı PR 4'te.

Karar: Event fiziksel silinmeyecek; `status=CANCELLED` ve `cancelled_at` ile iptal edilecek, aktif reservation'lar aynı kontrollü akışta `CANCELLED_BY_EVENT` durumuna geçecek.

Değerlendirdiğim alternatifler: Hard delete/cascade; event'i değişmeden bırakıp yalnız UI'da gizlemek.

Neden bunu seçtim: Reservation geçmişi, audit izi ve referential integrity korunur; iptal semantiği açık olur.

Neyi feda ettim: Bütün public/owner sorguları status politikasını bilinçli uygulamalı; storage zamanla büyür.

## D-008 — Immutable PostgreSQL audit

Durum: Tablo ve UPDATE/DELETE trigger'ı PR 1'de; kritik writer'lar PR 3-4'te.

Karar: Kritik audit satırı domain değişikliğiyle aynı transaction'da insert edilecek; uygulama rolü dahil UPDATE/DELETE trigger tarafından reddedilecek.

Değerlendirdiğim alternatifler: Uygulama logu; ayrı queue/service; değiştirilebilir history tablosu; database CDC.

Neden bunu seçtim: Başarılı domain commit'i auditsiz kalamaz ve uygulama hatası geçmişi sessizce değiştiremez.

Neyi feda ettim: Audit düzeltmesi yerinde update ile yapılamaz; düzeltici yeni kayıt/operasyon gerekir ve tablo retention planı ister.

## D-009 — Kısa ömürlü access JWT ve opaque rotating refresh token

Durum: PR 2'de uygulandı; access/refresh ve saldırgan integration testleriyle kanıtlandı.

Karar: Access credential kısa ömürlü JWT; refresh credential yüksek entropili opaque token olacak, yalnız SHA-256 hash'i saklanacak ve her kullanımdan sonra rotate edilecek.

Değerlendirdiğim alternatifler: Uzun ömürlü JWT; refresh JWT; server-side session cookie; raw refresh token saklamak.

Neden bunu seçtim: Access doğrulaması stateless kalırken refresh revoke/replay kontrolü server-side yapılabilir; DB sızıntısı raw tokenı doğrudan vermez.

Neyi feda ettim: Rotation transaction ve frontend single-flight bootstrap karmaşıklığı oluşur; access token süresi dolana kadar anlık revoke garanti edilmez.

## D-010 — Redis yalnız rate limiting state'i için

Durum: Compose PR 1'de; login limiti PR 2'de uygulandı, reservation limiti PR 4'te.

Karar: Redis, IP+normalized-email login ve authenticated-user reservation rate limit sayaçlarını paylaşacak; domain cache veya doğruluk kaynağı olmayacak.

Değerlendirdiğim alternatifler: Process memory; PostgreSQL counter; edge provider rate limit; Redis domain cache.

Neden bunu seçtim: Replica'lar arasında ortak, kısa ömürlü ve atomik sayaç sağlarken Redis kaybı domain verisini tutarsız bırakmaz.

Neyi feda ettim: Ek runtime dependency ve readiness kontrolü gerekir; limit politikasının fail-open/fail-closed davranışı test edilmelidir.

## D-011 — Yalnız `nextCursor` döndüren cursor pagination

Durum: API PR 3, route-level client history PR 5'te.

Karar: Liste API'si stabil sort tuple içeren opaque `nextCursor` döndürecek; geri navigasyon frontend'in route-level cursor geçmişinden yapılacak.

Değerlendirdiğim alternatifler: Offset/page-number; API `previousCursor`; tüm sonuçları client'a yüklemek.

Neden bunu seçtim: Concurrent insertlerde offset kayması azalır ve server cursor sözleşmesi tek yönlü, küçük kalır.

Neyi feda ettim: Rastgele sayfaya atlama yoktur; hard refresh ilk sayfaya döner ve client cursor stack yönetir.

## D-012 — Seed edilmiş kategori kataloğu

Durum: PR 1'de uygulandı.

Karar: Kategoriler ayrı, idempotent seed komutuyla kararlı UUID/slug değerleriyle üretilecek; migration DDL dışında katalog verisi taşımayacak.

Değerlendirdiğim alternatifler: Enum; migration içine insert; organizer'ın serbest metin kategorisi; runtime startup seed'i.

Neden bunu seçtim: Katalog ilişkisel/filtrelenebilir kalır, seed tekrar çalıştırılabilir ve şema sürümünden bağımsız evrilir.

Neyi feda ettim: Deployment migration sonrasında ayrı seed başarı koşuluna ihtiyaç duyar; katalog yönetim UI'sı bu kapsamda yoktur.

## D-013 — Prometheus, Loki, Alloy ve Grafana pipeline'ı

Durum: Karar kabul edildi; provisioning ve smoke testleri PR 6 P2'de.

Karar: Metrikler Prometheus uyumlu endpoint'ten, container JSON logları Alloy üzerinden Loki'ye taşınacak; Grafana datasource/dashboard'ları repository dosyalarıyla provision edilecek.

Değerlendirdiğim alternatifler: Yalnız Docker logs; ELK; OpenTelemetry collector + vendor SaaS; manuel Grafana kurulumu.

Neden bunu seçtim: Lokal/ücretsiz, tekrar üretilebilir ve metrik-log korelasyonunu gösteren bir teslim sağlar; harici ücretli servise bağımlı değildir.

Neyi feda ettim: Compose kaynak tüketimi ve provisioning bakımı artar; full tracing bu kapsamda yoktur.

## D-014 — KVKK için anonimleştirme politikası

Durum: Politika PR 1'de; account deletion endpoint'i P0 kapsamında değildir.

Karar: Silme talebinde email/full name anonimleştirilecek, password etkisizleştirilecek ve hesap girişe kapatılacak, bütün refresh tokenlar revoke edilecek; reservation/audit foreign key'leri anonim UUID üzerinde korunacak ve audit satırları değişmeyecek.

Değerlendirdiğim alternatifler: User ve ilişkileri hard delete/cascade; hiçbir kişisel alanı değiştirmemek; audit satırlarını yeniden yazmak.

Neden bunu seçtim: Ürün geçmişi ve kritik audit bütünlüğü korunurken doğrudan kimliklendiren hesap alanları kaldırılabilir.

Neyi feda ettim: Bu teknik politika tek başına hukuki retention kararı değildir; süreler ve dolaylı tanımlayıcılar hukuk/operasyon ekipleriyle belirlenmelidir.

## D-015 — Loki düşük-cardinality label ve 7 günlük lokal retention

Durum: Karar kabul edildi; PR 6 P2'de uygulanacak.

Karar: Loki label'ları `service_name`, `environment`, `level` ve gerekirse route template ile sınırlı olacak; request/user/event/email alanları JSON field kalacak. Lokal demo retention varsayılan 7 gün olacaktır.

Değerlendirdiğim alternatifler: Request ID ve resource ID'leri label yapmak; limitsiz retention; yalnız grep edilebilir dosya logu.

Neden bunu seçtim: Index cardinality ve disk büyümesi kontrol altında kalırken LogQL JSON filtresiyle request korelasyonu sürer.

Neyi feda ettim: Request ID araması label lookup kadar ucuz değildir; production retention ayrı kapasite ve mevzuat değerlendirmesi ister.

## D-016 — Refresh token family, kilit ve replay revoke

Durum: PR 2'de satır kilitli transaction, concurrent replay testi ve aktif-family güvenli cleanup ile uygulandı.

Karar: Her login yeni `family_id` başlatacak; rotation önce transaction advisory lock ile family'yi, sonra eski token satırını kilitleyip nullable self-FK `replaced_by_id` zinciri kuracak. Eski token replay'i aynı family'nin bütün aktif tokenlarını revoke edecek.

Değerlendirdiğim alternatifler: Her tokenı bağımsız revoke; reuse detection olmadan rotation; Redis session; replacement zinciri olmadan tek current-token alanı.

Neden bunu seçtim: Token çalınması/reuse görünür olur, eşzamanlı rotation tek kazanana iner ve kullanıcı zinciri adli olarak izlenebilir.

Neyi feda ettim: Normal concurrent refresh'lerden biri replay alarmına dönüşebilir; frontend single-flight ve dikkatli row-lock transaction gerekir. Cleanup aktif family zincirini bozamaz.

## D-017 — Idempotency snapshot ve request ID ayrımı

Durum: Şema PR 1'de; request-ID-free snapshot, güncel replay ID enjeksiyonu ve original ID header'ı PR 4'te uygulandı.

Karar: Stored response snapshot request/correlation ID içermeyecek. Her replay güncel `X-Request-ID` değerini header ve hata body'sine enjekte edecek; ilk owner ID yalnız `Idempotency-Original-Request-ID` header'ında korunacak.

Değerlendirdiğim alternatifler: İlk response body/header'ını byte-for-byte saklamak; replay'de yalnız original ID; correlation bilgisini hiç döndürmemek.

Neden bunu seçtim: Her HTTP denemesi kendi log zinciriyle korele olurken semantic status/body sonucu aynı kalır ve ilk domain işlemi ayrıca izlenebilir.

Neyi feda ettim: Replay serializer stored snapshot'ı bilinçli yeniden kurmalıdır; ham response cache daha basit olurdu.

## D-018 — ISO offset, IANA timezone ve DST kabul politikası

Durum: Server validation PR 3'te uygulandı; client validation PR 5'te.

Karar: Event create/PATCH timestamp'inin açık ISO-8601 offset'i, seçilen IANA timezone'un aynı instanttaki gerçek offset'iyle eşleşmelidir. DST gap reddedilir; fold yalnız gönderilen offset geçerli seçeneklerden biri ise kabul edilir.

Değerlendirdiğim alternatifler: Offset'i görmezden gelmek; server'ın sessizce düzeltmesi; yalnız browser validation; naive local datetime kabulü.

Neden bunu seçtim: Kullanıcının niyeti sessizce başka instante kaymaz ve frontend/backend timezone veritabanı farkları açık `422` ile görünür olur.

Neyi feda ettim: Request sözleşmesi daha katıdır; timezone kütüphanesi ve gap/fold test matrisi gerekir.

## D-019 — Organizer için owner-scoped detail endpoint'i

Durum: Owner-scoped API PR 3'te uygulandı; organizer ekranları PR 5'te.

Karar: Organizer edit/detail akışı public event detail kullanmayacak; `GET /api/v1/me/events/{eventId}` server-side ownership kontrolü yapacak ve başka organizatörün kaynağında gizleyen `404` döndürecek.

Değerlendirdiğim alternatifler: Public detail'i alıp UI'da owner kontrolü; tek detail endpoint'inde role göre değişen response; istemcinin organizer ID karşılaştırması.

Neden bunu seçtim: Yönetim verisi ve authorization sınırı açık olur; public projection'ın edit için yetersiz veya fazla veri taşıması önlenir.

Neyi feda ettim: Benzer event projection'ları ve ek endpoint/test bakımı oluşur; frontend iki farklı query key kullanır.

## D-020 — Browser access tokenı yalnız process belleğinde

Durum: PR 5'te memory-only token store, refresh-cookie bootstrap ve single-flight retry ile uygulandı.

Karar: Access JWT `localStorage`, `sessionStorage` veya kalıcı cookie'ye yazılmayacak; yalnız frontend modül belleğinde tutulacak. HttpOnly refresh cookie ile reload bootstrap yapılacak. Eşzamanlı korumalı `401` yanıtları tek refresh çağrısını paylaşacak ve özgün `Request` yeni Bearer token ile yeniden gönderilecek.

Değerlendirdiğim alternatifler: Access tokenı localStorage/sessionStorage'da saklamak; bütün kimliği JavaScript tarafından okunabilir cookie'ye koymak; her `401` için bağımsız refresh; otomatik retry yapmamak.

Neden bunu seçtim: XSS durumunda kalıcı access credential okuma yüzeyi azalır; refresh credential JavaScript'e açılmaz; token rotation yarışı sınırlanır. Özgün `Request` replay'i reservation `Idempotency-Key` başlığını retry boyunca korur.

Neyi feda ettim: Her tam sayfa yüklemesi bir refresh çağrısı gerektirir; ayrı browser tabları process belleğini paylaşmaz ve kendi bootstrap'ını yapar. Refresh servisi geçici olarak erişilemezse mevcut access token kalıcı depodan kurtarılamaz.

## D-021 — Seed yalnız eksik demo kayıtlarını ekler

Durum: PR 5 P0 yeniden denetiminde uygulandı ve domain durumu korunumu integration testiyle doğrulandı.

Karar: Seed komutu kararlı kimlikli demo kullanıcı, etkinlik ve rezervasyon kayıtlarını yalnız mevcut değillerse ekleyecek; mevcut domain kayıtlarını güncellemeyecek. Kategori kataloğu adları ise seed tarafından yönetildiği için güncellenebilir.

Değerlendirdiğim alternatifler: Her çalışmada bütün seed alanlarını ilk değerlere döndürmek; `reserved_count` değerini seed sonunda aktif rezervasyonlardan yeniden hesaplamak; seed öncesinde tabloları temizlemek.

Neden bunu seçtim: Tekrar çalıştırılan deployment seed'i organizatör değişikliklerini, iptalleri, kullanıcı durumunu veya rezervasyon yaşam döngüsünü geri alamaz ve `reserved_count == ACTIVE reservations` invariantını bozamaz.

Neyi feda ettim: Demo içerik metinlerindeki sonraki seed değişiklikleri mevcut ortama otomatik uygulanmaz; böyle bir yenileme için açık ve ayrı bir bakım komutu gerekir.

## D-022 — Swagger UI varlıkları backend tarafından sunulur

Durum: PR 5 P0 dokümantasyon doğrulamasında uygulandı ve HTML/statik varlık integration testiyle güvenceye alındı.

Karar: Geliştirme ve test ortamlarındaki Apache-2.0 lisanslı Swagger UI `5.32.11` JavaScript, CSS ve favicon dosyaları backend imajında sabit sürümle paketlenecek ve `/docs-assets` üzerinden aynı origin'den sunulacak. OpenAPI `3.1.0` şeması `/api/v1/openapi.json` adresinde kalacak; production ortamında etkileşimli dokümantasyon kapalı kalacaktır.

Değerlendirdiğim alternatifler: FastAPI'nin varsayılan jsDelivr CDN bağlantılarını kullanmak; yalnız ham OpenAPI JSON sunmak; production'da da Swagger UI açmak.

Neden bunu seçtim: Yerel geliştirme, kapalı ağ ve CDN engeli durumlarında `/docs` boş kalmaz; dokümantasyon render'ı üçüncü taraf çalışma zamanı erişimine bağlı olmaz.

Neyi feda ettim: Backend imajı Swagger statik dosyaları nedeniyle büyür ve paket sürümü ayrıca güncellenmelidir; production kullanıcıları şemayı kullanır fakat etkileşimli UI görmez.

## D-023 - Event araması generated Türkçe tsvector kullanır

Durum: PR 6 P1'de migration, API, query-plan ve frontend filtre testleriyle uygulandı.

Karar: Event başlığı A, açıklaması B ağırlığıyla PostgreSQL tarafından üretilen stored `tsvector` alanında `pg_catalog.turkish` yapılandırmasıyla indekslenecek; arama `websearch_to_tsquery` ve GIN üzerinden çalışacak. Kategori slug ile, tarih aralığı ise her etkinliğin kendi IANA saat dilimindeki dahil yerel takvim günüyle filtrelenecek. Cursor bütün normalize filtrelerin hash'ine bağlanacak.

Değerlendirdiğim alternatifler: `ILIKE '%q%'`; harici arama servisi; UTC gününe göre tarih filtresi; filtrelerden bağımsız cursor; her filtre kombinasyonu için ek B-tree indeksleri.

Neden bunu seçtim: Modüler monolit sınırı korunur, Türkçe kelime çözümleme PostgreSQL içinde deterministik kalır, GIN başlık/açıklama taramasını ölçekler ve kullanıcı farklı saat dilimindeki etkinlikleri etkinliğin ilan edilen yerel gününe göre bulur. Filtre hash'i eski cursor'ın yeni sorguda kayıt atlamasını veya tekrarlamasını önler.

Neyi feda ettim: Event yazımları generated vector ve GIN bakım maliyeti taşır; yerel tarih ifadesi satır başına timezone dönüşümü yaptığı için ayrı bir indeks kullanmaz. Katalog ölçeği büyürse ölçüme dayalı expression index veya farklı arama mimarisi ayrıca değerlendirilmelidir.
