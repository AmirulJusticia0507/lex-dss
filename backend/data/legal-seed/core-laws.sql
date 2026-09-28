-- Starter corpus for legal_articles.
-- Run after alembic upgrade head.

CREATE UNIQUE INDEX IF NOT EXISTS ux_legal_articles_document_article
ON legal_articles (document_title, article_number);

INSERT INTO legal_articles (document_title, article_number, domain, hierarchy_id, content, meta_data)
SELECT seed.document_title,
       seed.article_number,
       seed.domain,
       lh.id,
       seed.content,
       seed.meta_data::jsonb
FROM (
    VALUES
    (
        'Undang-Undang Nomor 1 Tahun 2023 tentang Kitab Undang-Undang Hukum Pidana',
        '1',
        'criminal',
        'UU',
        '(1) Suatu perbuatan tidak dapat dipidana, kecuali berdasarkan kekuatan ketentuan peraturan perundang-undangan pidana yang telah ada sebelum perbuatan dilakukan.
(2) Dalam menetapkan adanya tindak pidana dilarang digunakan analogi.',
        '{"act":"UU 1/2023","status":"berlaku","effective_date":"2026-01-02","source_url":"https://peraturan.go.id/id/uu-no-1-tahun-2023","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 1 Tahun 2023 tentang Kitab Undang-Undang Hukum Pidana',
        '38',
        'criminal',
        'UU',
        'Setiap Orang yang pada waktu melakukan Tindak Pidana menyandang disabilitas mental dan/atau disabilitas intelektual dapat dikurangi pidananya dan/atau dikenai tindakan.',
        '{"act":"UU 1/2023","status":"berlaku","effective_date":"2026-01-02","source_url":"https://peraturan.go.id/id/uu-no-1-tahun-2023","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Kitab Undang-Undang Hukum Perdata',
        '1320',
        'civil',
        'UU',
        'Supaya terjadi persetujuan yang sah, perlu dipenuhi empat syarat: kesepakatan mereka yang mengikatkan dirinya; kecakapan untuk membuat suatu perikatan; suatu pokok persoalan tertentu; dan suatu sebab yang tidak terlarang.',
        '{"act":"KUHPerdata","source_url":"https://peraturan.bpk.go.id/Details/17229/kuhperdata","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Kitab Undang-Undang Hukum Perdata',
        '1338',
        'civil',
        'UU',
        'Semua persetujuan yang dibuat sesuai dengan undang-undang berlaku sebagai undang-undang bagi mereka yang membuatnya. Persetujuan itu tidak dapat ditarik kembali selain dengan kesepakatan kedua belah pihak, atau karena alasan-alasan yang ditentukan oleh undang-undang. Persetujuan harus dilaksanakan dengan itikad baik.',
        '{"act":"KUHPerdata","source_url":"https://peraturan.bpk.go.id/Details/17229/kuhperdata","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Kitab Undang-Undang Hukum Perdata',
        '1365',
        'civil',
        'UU',
        'Tiap perbuatan yang melanggar hukum dan membawa kerugian kepada orang lain mewajibkan orang yang karena salahnya menerbitkan kerugian itu mengganti kerugian tersebut.',
        '{"act":"KUHPerdata","source_url":"https://peraturan.bpk.go.id/Details/17229/kuhperdata","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 12 Tahun 2011 tentang Pembentukan Peraturan Perundang-undangan',
        '7',
        'constitutional',
        'UU',
        '(1) Jenis dan hierarki Peraturan Perundang-undangan terdiri atas: Undang-Undang Dasar Negara Republik Indonesia Tahun 1945; Ketetapan Majelis Permusyawaratan Rakyat; Undang-Undang/Peraturan Pemerintah Pengganti Undang-Undang; Peraturan Pemerintah; Peraturan Presiden; Peraturan Daerah Provinsi; dan Peraturan Daerah Kabupaten/Kota.
(2) Kekuatan hukum Peraturan Perundang-undangan sesuai dengan hierarki sebagaimana dimaksud pada ayat (1).',
        '{"act":"UU 12/2011","source_url":"https://peraturan.go.id/id/uu-no-12-tahun-2011","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 48 Tahun 2009 tentang Kekuasaan Kehakiman',
        '3',
        'judiciary',
        'UU',
        '(1) Dalam menjalankan tugas dan fungsinya, hakim dan hakim konstitusi wajib menjaga kemandirian peradilan.
(2) Segala campur tangan dalam urusan peradilan oleh pihak lain di luar kekuasaan kehakiman dilarang, kecuali dalam hal-hal sebagaimana dimaksud dalam Undang-Undang Dasar Negara Republik Indonesia Tahun 1945.',
        '{"act":"UU 48/2009","source_url":"https://peraturan.go.id/id/uu-no-48-tahun-2009","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 48 Tahun 2009 tentang Kekuasaan Kehakiman',
        '5',
        'judiciary',
        'UU',
        '(1) Hakim dan hakim konstitusi wajib menggali, mengikuti, dan memahami nilai-nilai hukum dan rasa keadilan yang hidup dalam masyarakat.
(2) Hakim dan hakim konstitusi harus memiliki integritas dan kepribadian yang tidak tercela, jujur, adil, profesional, dan berpengalaman di bidang hukum.
(3) Hakim dan hakim konstitusi wajib menaati Kode Etik dan Pedoman Perilaku Hakim.',
        '{"act":"UU 48/2009","source_url":"https://peraturan.go.id/id/uu-no-48-tahun-2009","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 48 Tahun 2009 tentang Kekuasaan Kehakiman',
        '10',
        'judiciary',
        'UU',
        '(1) Pengadilan dilarang menolak untuk memeriksa, mengadili, dan memutus suatu perkara yang diajukan dengan dalih bahwa hukum tidak ada atau kurang jelas, melainkan wajib untuk memeriksa dan mengadilinya.
(2) Ketentuan sebagaimana dimaksud pada ayat (1) tidak menutup usaha penyelesaian perkara perdata secara perdamaian.',
        '{"act":"UU 48/2009","source_url":"https://peraturan.go.id/id/uu-no-48-tahun-2009","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 49 Tahun 2009 tentang Peradilan Umum',
        '50',
        'judiciary',
        'UU',
        'Pengadilan Negeri bertugas dan berwenang memeriksa, memutus, dan menyelesaikan perkara pidana dan perkara perdata di tingkat pertama.',
        '{"act":"UU 49/2009","source_url":"https://peraturan.go.id/id/uu-no-49-tahun-2009","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 5 Tahun 1986 tentang Peradilan Tata Usaha Negara',
        '47',
        'administrative',
        'UU',
        'Pengadilan bertugas dan berwenang memeriksa, memutus, dan menyelesaikan sengketa Tata Usaha Negara.',
        '{"act":"UU 5/1986","source_url":"https://peraturan.go.id/id/uu-no-5-tahun-1986","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    ),
    (
        'Undang-Undang Nomor 3 Tahun 2009 tentang Mahkamah Agung',
        '31A',
        'judiciary',
        'UU',
        'Permohonan pengujian peraturan perundang-undangan di bawah undang-undang terhadap undang-undang diajukan langsung oleh pemohon atau kuasanya kepada Mahkamah Agung.',
        '{"act":"UU 3/2009","source_url":"https://peraturan.go.id/id/uu-no-3-tahun-2009","transcription_status":"manual_starter_excerpt","verification_status":"not_independently_legal_reviewed"}'
    )
) AS seed(document_title, article_number, domain, hierarchy_type, content, meta_data)
JOIN legal_hierarchy lh ON lh.type_name = seed.hierarchy_type
ON CONFLICT (document_title, article_number) DO UPDATE
SET domain = EXCLUDED.domain,
    hierarchy_id = EXCLUDED.hierarchy_id,
    content = EXCLUDED.content,
    meta_data = EXCLUDED.meta_data,
    embedding = NULL,
    updated_at = now();
