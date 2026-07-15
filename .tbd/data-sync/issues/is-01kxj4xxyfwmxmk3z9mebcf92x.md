---
type: is
id: is-01kxj4xxyfwmxmk3z9mebcf92x
title: Modernize and validate Deep Transcribe end to end
kind: epic
status: open
priority: 1
version: 33
labels:
  - deep-transcribe-modernization
dependencies: []
child_order_hints:
  - is-01kgrwrwpe7nn5m6zvc4mkpsp4
  - is-01kgrws40k5wmfz5sddz8whbvy
  - is-01kgrx3az4cdkhd04xzq23n2zz
  - is-01kgt1rvd6maej0g7w3qef15bt
  - is-01kgt1s3c9wtt7ytpkaz1j53s3
  - is-01kxa4n2ngtn4sthy8cm7gkzyv
  - is-01kxf3q82h8nyx7k4kjjhk27yr
  - is-01kxhe5pq7df6tyah55ydk77ay
  - is-01kxhkv8bbgp650a4bzxxp63nq
  - is-01kxhs6cd2dek60wvv6h290z03
  - is-01kgrws7my5fefbghn3b62fg75
  - is-01kgrwsb472am6345sp2fvghp8
  - is-01kgrwsf1seq1sg228y2zrx1nv
  - is-01kgrwvpp4pwx1bhdebw7xe8hp
  - is-01kgt1sb0sgwmtdrdp56ypd7fy
  - is-01kgt1sj7yjfpqqyvndsynexfm
  - is-01kgt1sv77mrswqjdwcg1xjpjr
  - is-01kxa5cf2nzw63npnfwmkcqagj
  - is-01kxa5cfax7r8hcjzt5c0xc1kg
  - is-01kgt1t48awntstmf753x7mg05
  - is-01kxj4zk78w2hqjxhg70jcrbyd
  - is-01kxj4zkkb6e68kpa6x3bvs2zp
  - is-01kxj4zkw8vp8g4ebs496hwdgw
  - is-01kxj5t1w964tpzxfx8eacf734
  - is-01kxj8kybch3y98k47rphvdw9z
  - is-01kxj951e67pw82pex30hhhj74
  - is-01kxja8jm21m1a0jyw0tdc7aqv
  - is-01kxjaq0b6qbc56qsyemfq06qa
  - is-01kxjaq0ksv5jkjkm9r02x38wt
  - is-01kxjaq0trtms6w1nqbkrq2yxd
  - is-01kxjar0zn3a684rf5qnb1nvcn
created_at: 2026-07-15T05:45:24.686Z
updated_at: 2026-07-15T07:27:02.644Z
---
Coordinate dependency/model modernization across Deep Transcribe, kash-shell, kash-docs, and kash-media; Deepgram settings; startup/install weight; source context and speaker correction; URL/local-media fixes; zero-install skill/docs; patch releases; and release-grade end-to-end validation.

## Notes

Implementation is merged and patch releases are published: kash-shell 0.4.6, kash-media 0.4.4, deep-transcribe 0.1.9. Global uv tool was uninstalled and reinstalled at 0.1.9; dependency tree contains no Torch and help starts in 0.05-0.07s. All legacy Beads issues were imported and validated in tbd before the obsolete .beads store was removed. Only README fixture approval remains.
