//! The end-to-end faithful gate: the library run orchestration
//! reproduces every golden `.cli` byte-for-byte from the typed run
//! inputs of SPEC-RUNSPEC's golden equivalence table. Stage C wires
//! the same inputs through the `inp.yaml`/CLI surface.

use cligen::modes::{run_to_cli, RunInputs};
use cligen::profile::GenerationProfile;
use cligen::storm::SingleStormParams;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

struct Golden {
    name: &'static str,
    par: &'static str,
    prn: Option<&'static str>,
    iopt: i32,
    interp: i32,
    burn: u32,
    begin_year: Option<i32>,
    years: Option<i32>,
    storm: bool,
    echo: &'static str,
}

const SS: SingleStormParams = SingleStormParams {
    mo: 6,
    jd: 15,
    ibyear: 12,
    damt: 2.25,
    usdur: 6.0,
    ustpr: 0.4,
    uxmav: 1.5,
};

const GOLDENS: [Golden; 12] = [
    Golden {
        name: "new-meadows-id-seed0",
        par: "new-meadows-id/id106388.par",
        prn: None,
        iopt: 5,
        interp: 0,
        burn: 0,
        begin_year: Some(1),
        years: Some(31),
        storm: false,
        echo: "-iid106388.par",
    },
    Golden {
        name: "new-meadows-id-seed17",
        par: "new-meadows-id/id106388.par",
        prn: None,
        iopt: 5,
        interp: 0,
        burn: 17,
        begin_year: Some(1),
        years: Some(31),
        storm: false,
        echo: "-r17 -iid106388.par",
    },
    Golden {
        name: "jeogla-au-seed0",
        par: "jeogla-au/ASN00057011.par",
        prn: None,
        iopt: 5,
        interp: 0,
        burn: 0,
        begin_year: Some(1),
        years: Some(42),
        storm: false,
        echo: "-iASN00057011.par",
    },
    Golden {
        name: "jeogla-au-seed17",
        par: "jeogla-au/ASN00057011.par",
        prn: None,
        iopt: 5,
        interp: 0,
        burn: 17,
        begin_year: Some(1),
        years: Some(42),
        storm: false,
        echo: "-r17 -iASN00057011.par",
    },
    Golden {
        name: "mt-wilson-ca-observed-seed0",
        par: "mt-wilson-ca/ca046006.par",
        prn: Some("fixtures/mt-wilson-ca/ws.prn"),
        iopt: 6,
        interp: 2,
        burn: 0,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-ica046006.par -Ows.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "mt-wilson-ca-observed-seed17",
        par: "mt-wilson-ca/ca046006.par",
        prn: Some("fixtures/mt-wilson-ca/ws.prn"),
        iopt: 6,
        interp: 2,
        burn: 17,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-r17 -ica046006.par -Ows.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "fish-springs-ut-observed-padded-seed0",
        par: "fish-springs-ut/ut422852.par",
        prn: Some("fixtures/fish-springs-ut/ws.prn"),
        iopt: 6,
        interp: 2,
        burn: 0,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-iut422852.par -Ows.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "fish-springs-ut-observed-padded-seed17",
        par: "fish-springs-ut/ut422852.par",
        prn: Some("fixtures/fish-springs-ut/ws.prn"),
        iopt: 6,
        interp: 2,
        burn: 17,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-r17 -iut422852.par -Ows.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "fish-springs-ut-observed-truncated-seed0",
        par: "fish-springs-ut/ut422852.par",
        prn: Some(
            "docs/work-packages/20260709-golden-fixture-harness/artifacts/inputs/fish-springs-ut/ws-truncated.prn",
        ),
        iopt: 6,
        interp: 2,
        burn: 0,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-iut422852.par -Ows-truncated.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "fish-springs-ut-observed-truncated-seed17",
        par: "fish-springs-ut/ut422852.par",
        prn: Some(
            "docs/work-packages/20260709-golden-fixture-harness/artifacts/inputs/fish-springs-ut/ws-truncated.prn",
        ),
        iopt: 6,
        interp: 2,
        burn: 17,
        begin_year: None,
        years: None,
        storm: false,
        echo: "-r17 -iut422852.par -Ows-truncated.prn -owepp.cli -t6 -I2",
    },
    Golden {
        name: "new-meadows-id-single-storm-seed0",
        par: "new-meadows-id/id106388.par",
        prn: None,
        iopt: 4,
        interp: 0,
        burn: 0,
        begin_year: None,
        years: None,
        storm: true,
        echo: "-iid106388.par -t4 -owepp.cli",
    },
    Golden {
        name: "new-meadows-id-single-storm-seed17",
        par: "new-meadows-id/id106388.par",
        prn: None,
        iopt: 4,
        interp: 0,
        burn: 17,
        begin_year: None,
        years: None,
        storm: true,
        echo: "-r17 -iid106388.par -t4 -owepp.cli",
    },
];

/// The endgame gate: 12/12 golden `.cli` files reproduced
/// byte-identically from typed run inputs.
#[test]
fn goldens_reproduced_byte_identically() {
    let root = repo_root();
    for g in &GOLDENS {
        let par_bytes = std::fs::read(root.join("fixtures").join(g.par)).unwrap();
        let prn_bytes = g.prn.map(|rel| std::fs::read(root.join(rel)).unwrap());
        let got = run_to_cli(&RunInputs {
            iopt: g.iopt,
            interp: g.interp,
            burn: g.burn,
            generation_profile: GenerationProfile::Faithful5323,
            begin_year: g.begin_year,
            years: g.years,
            par_bytes: &par_bytes,
            prn_bytes: prn_bytes.as_deref(),
            storm: g.storm.then_some(SS),
            version: 5.3230,
            command_echo: g.echo,
        })
        .unwrap_or_else(|e| panic!("{}: run failed: {e}", g.name));
        let golden = std::fs::read(
            root.join("docs/work-packages/20260709-golden-fixture-harness/artifacts/goldens")
                .join(format!("{}.cli", g.name)),
        )
        .unwrap();
        let got_bytes = got.cli.as_bytes();
        if got_bytes != golden.as_slice() {
            // Localize: first divergent line.
            let got_lines: Vec<&str> = got.cli.lines().collect();
            let golden_text = String::from_utf8_lossy(&golden);
            let golden_lines: Vec<&str> = golden_text.lines().collect();
            for (i, (a, b)) in got_lines.iter().zip(&golden_lines).enumerate() {
                assert_eq!(
                    a,
                    b,
                    "{}: first divergent line {} (got vs golden)",
                    g.name,
                    i + 1
                );
            }
            panic!(
                "{}: line counts differ: got {} golden {}",
                g.name,
                got_lines.len(),
                golden_lines.len()
            );
        }
    }
}
