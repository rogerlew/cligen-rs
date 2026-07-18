# R7 legacy log-normalization receipt

The twelve Slurm `.err` diagnostics each contained exactly two producer-made
`<REMOTE_RUN_ROOT>` labels and no `<JOB_LOCAL>` labels. The exact 24 strings
were changed to `[REMOTE_RUN_ROOT]` before the successful collection download.
Scientific JSON, stdout, checkpoints, gate receipts, and accounting were not
changed.

| Diagnostic | Original SHA-256 | Collected SHA-256 |
|---|---|---|
| n0-l32-d2-gpd | `ab0e6c46ad7b679d02b09f1220dd9d877a58caa0cfe7bc348392ccaf5133ffec` | `dc87a8a8989699dfb45b45a19dcc4396774086d9bca48b139cae324f8ab9f1f8` |
| n0-l32-d2-lognormal | `24635e876a15b2449697d443016630a200abf9fca55a18ba4d5e94b84671a294` | `40fa142b1585debb7cf97822809f8640dfe2f40431a633b66d26b399a065f56c` |
| n0-l64-d2-gpd | `da1466b3d64212a44d7e9af040be731b3384868920c8f7ac9b746d22bb9bed66` | `a6a013b8a326c14d5a507af187eb6bf1cd05ad9c5bc781fd14009c246e042e1a` |
| n0-l64-d2-lognormal | `410e085470c67fda20d8a0923b268ddfd1b3ad9c82c20c49d5235ebbff5d5363` | `dc6f4e078809e46c0480ae834967e0be7fdb373e2e2dac433b34d6b335131c38` |
| n0-l64-d3-gpd | `cadc2db6a551eaf6ae787d6509c03305c16deaa76fc45b27036245be5e5b7b79` | `fa97d1fb714448ba56ae9e73df029e4ce098719016bb89d67e4b0d987893bbae` |
| n0-l64-d3-lognormal | `52d1f5ae9403684b5946183d2cb979382e2d3ee8cf0dcd00bd34cc9cbbfa26b6` | `2801c92824e8191c11acc4a21303d0f097735d2d5f465b159856b234a151e0ec` |
| n1-l32-d2-gpd | `1fd3b7918714c9b31d636136b00b9536a4915c5c5d2d55dfb4b88a3fadb108e7` | `909349c190893e0bbcebe86b8f4c7e414735f0a92c289e79d64fa25484773529` |
| n1-l32-d2-lognormal | `e65a04ec28edfceb9bcc09d72be4abc2b20b5752093627591a192ad95b997cd8` | `13bfca64081e2a8df6aaf99f96e7a4ddd150c6da2185ff21b1fa9526f9523d66` |
| n1-l64-d2-gpd | `4d581a6d50e529904c1368a7f1b075bccf849be288c7ad8df94d0273cd193252` | `cb56b6e6f8e5d41dabad98acc3b7292f00e4f9d434321f1b49dce3ac986bf7db` |
| n1-l64-d2-lognormal | `61dce26f67cdf8594866e875352ffccd30724c41520d0a9822828792e254d988` | `a2a3fcfddea12fe6f5f0f5efb90c5fcd7ffce26183f6af305b9fb4fd3f803daf` |
| n1-l64-d3-gpd | `bba32d67ab570ce1112a74878f4068e26fd6be789a0c6e4dedcf0e47063d143b` | `46c620ab7187f1adbe2dcd6bd1c65b3138f7676b243db87a6bd7e7f97bb91b54` |
| n1-l64-d3-lognormal | `b3ffd1ece1c88c19d7c4235fd9157e77e734acb86d3864f5a18659dd36ad320f` | `d4e41a2264f306a380e97694e727b7664ebfbed3e1480f719e8014a497b2e989` |

The two failed quarantines retained the original bytes until authenticated
collection and cleanup completed. Toolkit close then intentionally purged all
restricted private run state; this hash receipt is the retained audit record.
