<!-- License: CC BY 4.0 (some pieces CC0). Reading, quoting in full, indexing, retrieval and training are permitted with attribution: Jed Anderson, jedanderson.org. -->
---
title: 'Stop Serving as the Wiring Between Machines'
subtitle: 'Why a 20-watt human brain that thinks at 10 bits per second and speaks at 39 to 56 bits per second makes a terrible serial cable—and how breaking a 50-year bottleneck frees people to actually protect the Earth.'
slug: 'stop-serving-as-the-wiring-between-machines'
date: 2026-11-12
type: 'essay'
status: 'published'
tags: ['enviroai', 'environmental-intelligence', 'information-theory', 'regulatory-reform', 'tceq', 'monitoring', 'landauer']
abstract: 'Environmental compliance still routes machine-generated numbers through human brains that consciously process 10 to 50 bits per second, because permits were written in English that software could not read. Drawing on Zheng & Meister''s bandwidth measurements and TCEQ''s FY 2025 enforcement record, the essay argues that this human-wire architecture consumes roughly 80% of compliance labor and drives about a quarter of formal Texas citations, and that AI reading of permits, continuous telemetry, and real-time payback now let people be unwired and returned to judgment.'
license: 'CC-BY-4.0'
author: 'Jed Anderson'
co_authors: []
canonical_url: 'https://jedanderson.org/essays/stop-serving-as-the-wiring-between-machines'
pdf: '/pdfs/stop-serving-as-the-wiring-between-machines.pdf'
hero_image: '/images/stop-serving-as-the-wiring-between-machines-hero.jpg'
hero_image_alt: 'Black poster with bold white and mint-green type reading ''You are too valuable to be the wire.'' Below, a white silhouette of a person holds a green cable stretched between a pressure gauge on the left and a checked-off document on the right. Tagline: ''Less copying. More judgment.'' enviro.ai logo at the bottom.'
supporting_files: []
---

I am a human. I love humans. But for more than a quarter-century of practicing environmental law, I watched brilliant, conscientious people spend their working lives doing a job no human being was ever built to do: serving as the biological patch cord between machines that speak numbers and permits that speak English.

**I'm a terrible wire.** My value is judgment. Not moving data.

Walk into almost any chemical plant, refinery, or municipal water system on a Tuesday afternoon. A transducer on a pipe or a stack analyzer measures a physical state and outputs a number. A person collects that reading. Another person retypes it into a spreadsheet. Someone opens an 800-page PDF permit to check a conditional threshold. Someone performs a unit conversion. Someone assembles a quarterly compliance table and keys it into a state web portal. Every person in that chain may be dedicated and competent, yet the architecture itself violates the first principles of information theory. Why does data already produced by one machine have to pass through a human brain before another machine can evaluate or act upon it?

## I. Why I Make a Terrible Copper Wire

*I have no desire to point out anyone else's limitations—so let me put my own three-pound brain on the laboratory bench.*

Examine the author of this essay as a piece of data-conveyance hardware. Inside my skull sits roughly 1.4 kilograms (3.0 pounds) of neural tissue comprising 86 billion neurons and some 100 trillion synaptic connections, all operating on a metabolic power budget of roughly 20 Watts (Azevedo & Herculano-Houzel 2009)—less power than a dim porch bulb. At the microscopic scale of ion channels and synapses, biophysicists estimate that the brain executes 10¹⁵ synaptic spike operations per second (and up to 10¹⁸ molecular operations per second across ~2.5 Petabytes of synaptic capacity).

Why, then, am I so painfully slow, lossy, and high-latency when asked to copy stack-gas numbers into an Excel workbook? In a landmark study in *Neuron*, "The Unbearable Slowness of Being: Why do we live at 10 bits/s?" (Zheng & Meister 2025), neuroscientists Jieyu Zheng and Markus Meister quantified the central bottleneck of human cognition. While my peripheral sensory receptors stream more than 11 million bits per second into my unconscious nervous system (vision alone contributes ~10⁷ bits/s, touch ~10⁶ bits/s, and hearing and olfaction ~10⁵ bits/s each), my conscious mind processes reality at a strict serial speed limit of 10 to 50 bits per second.

Every external input and output channel I possess is governed by that same narrow throat. When I read a screen at 250 words per minute, I absorb roughly 28 to 45 bits per second. When I speak aloud, my vocal tract conveys information at a universal human average of 39.15 bits per second—topping out near 56 bits per second (Coupé et al. 2019, *Science Advances*). When I type into a spreadsheet at 60 to 120 words per minute, my fingers transmit just 10 to 17 bits per second (Zheng & Meister 2025). Meanwhile, my working memory can hold only 4 to 7 discrete chunks at once before lossless recall collapses into transcription errors (Zenil et al. 2015).

Evolution did not build that million-to-one compression filter by mistake. On the Pleistocene savanna, an organism that consciously audited every blade of grass would be eaten before it moved; survival belonged to the brain that threw away 99.9999% of raw data to make one fast, high-level judgment. My intellect is a masterpiece for physical intuition, ethical responsibility, and creative synthesis—and a disaster when used as a serial cable. The goal is not to remove humans from environmental protection; it is to stop wasting 86 billion neurons on connections we should engineer.

## II. The Report Is Not the Event: Bonds, Bits, and the 240× Floor

*A completed report cannot reverse a chemical release that already happened, and a clean dashboard cannot fix a broken control device.*

Environmental protection begins in physical reality. A hydrocarbon plume vents from a relief valve. A solvent migrates through groundwater. A biological clarifier loses oxygen. A storage tank corrodes. A thermal oxidizer flame goes out. These are physical events governed by conservation of mass and the Second Law of Thermodynamics. A report merely describes an event; a database stores evidence about it; a permit states obligations concerning it. None of those is the event itself.

*Figure 1 (in the PDF): Thermodynamic asymmetry and the human bottleneck. At 300 K, breaking one C–H chemical bond (6.86 × 10⁻¹⁹ J) costs 240 times more energy than erasing one bit at Landauer's bound (2.87 × 10⁻²¹ J). Silicon links move 10⁹+ bits/s losslessly, whereas human conscious thought (10–50 bps) and oral or typed conveyance (10–56 bps) are built for meaning, not data transport.*

Physics explains why connecting information to physical operations before a release occurs is the highest-leverage act in stewardship. Every chemical transformation is denominated in chemical bonds: breaking a single carbon–hydrogen bond (413 kJ/mol) requires E_bond ≈ 6.86 × 10⁻¹⁹ Joules, whereas Rolf Landauer proved in 1961 that erasing one bit of information at 300 K requires a minimum heat dissipation of E_bit = k_BT ln 2 ≈ 2.870 × 10⁻²¹ Joules. Divide the two and you uncover an invariant floor of physical law: information is at least 240 times cheaper than chemical force ([The Bond-Bit Ratio](/essays/bond-bit-ratio)). In an industrial plant, that leverage operates through architectural gating ([The Physics of Zero-Cost Stewardship](/essays/the-physics-of-zero-cost-stewardship)): one timely, validated bit closes a valve or adjusts a furnace before megajoules of chemical energy escape into the sky. When we trap that bit inside a 10-bit-per-second human clerical queue, the report arrives weeks after the molecules are already gone.

## III. Why Couldn't We Wire a Pressure Gauge to an 800-Page Permit?

*Inside a pipe, both ends of the wire have spoken numbers since 1975. In compliance, one end speaks numbers while the other speaks English.*

Why didn't industry fix this thirty years ago? Because inside a chemical process unit, a pressure transmitter and a flow controller both speak Numbers—so engineers wired them together with 4–20 milliamp loops and digital buses in the 1970s. In environmental compliance, however, the equipment speaks Numbers (42 psig) while the permit, regulations, and laboratory reports speak English (800 pages of conditional legal prose specifying which equipment, operating modes, averaging periods, and test methods apply).

Where regulations and instruments spoke the same numerical language—such as EPA's 40 CFR Part 75 Acid Rain program (1993), which linked Continuous Emission Monitoring Systems (CEMS) and quality-assurance checks directly to electronic reporting (ECMPS)—automation worked beautifully. Everywhere else, because computers could not read legal prose, only a human brain could read both ends of the wire. So we turned environmental engineers and attorneys into human modems.

**The same person. A better use of their mind.**

Used as a 10-bps processor:

- Copy the reading.
- Convert the units.
- Calculate the average.
- Assemble the report.

Freed to protect:

- Question the measurement.
- Investigate the anomaly.
- Improve the process.
- Solve the problem.

## IV. How Much of Our Work—and Our Failures—Comes From This Bad Wire?

*When you force a 10-bit-per-second brain with a 4-chunk memory to carry industrial data, you lose 80% of your staff's time and cause 1 in 4 formal violations.*

What actually happens when an entire regulatory system relies on a biological wire that processes at 10 bits per second, conveys data at 10 to 56 bits per second, drops chunks when interrupted, and introduces weeks of latency between a physical event and a compliance check? When we examine industrial workflows alongside the Texas Commission on Environmental Quality (TCEQ) FY 2025 Annual Enforcement Report and federal EPA compliance data, the damage shows up in four distinct numbers:

- **~75–80%** of compliance staff work is just "wire" labor.
- **~25%** of formal Texas citations trace to information handling (FY 2025).
- **>50%** of routine water Significant Noncompliance flags are reporting failures (EPA).
- **9.6M lbs** of Texas air releases were hidden by latency in one audit (TCEQ, p. 33).

**1. Almost four-fifths of human compliance work (~75%–80%) is just being the wire.** Walk through the week of an environmental engineer or consultant managing air permits, wastewater Discharge Monitoring Reports (DMRs), or Texas's 95,874 annual Tier II chemical inventories (TCEQ FY 2025, p. 42). Roughly 75% to 80% of their professional hours are spent gathering files, rekeying lab numbers, converting units, cross-checking permit clauses, and formatting submittals—leaving barely 20% of their time to walk the plant, question dubious sensor proxies, or fix equipment.

**2. One in four formal enforcement citations (~25%)—and over half of routine violations—come from the wire breaking.** In FY 2025, TCEQ issued 1,188 formal enforcement orders and civil judgments encompassing 3,267 alleged violations and 6,349 rule citations, plus 19,049 informal Notices of Violation (pp. 11, 19). While agencies code citations by legal rule rather than root cause (making any single number a reasoned structural estimate rather than a measured historical fact), decomposing TCEQ's top-cited rules shows that roughly 25% of formal citations (range 15%–35%) occur because a human wire failed to sample on schedule, copy a record, track a threshold, or file a notice. Indeed, 70% of all formal TCEQ violations are classified as "Moderate" severity (p. 20)—a category defined by failures to monitor, test, or maintain and submit records. In broader routine compliance, the share is even higher: TCEQ's 19,049 Notices of Violation spiked in FY 2025 due to missed lead service-line inventories and public notices, while nationally, EPA drinking-water records show four times as many water systems with monitoring and reporting violations (29.6%) as health-based violations (7.0%), and missing Discharge Monitoring Reports account for over half of Clean Water Act Significant Noncompliance (GAO-21-290).

*Figure 2 (in the PDF): The cost of using a 10-bps human wire. While direct wire failures cause ~5%–10% of physical release mass, they drive ~25% of formal Texas enforcement citations, ~30%–35% of all recorded violations, >50% of federal water SNC flags, and ~75%–80% of staff compliance hours. Across 60.8M lbs of FY 2025 Texas air emissions (TCEQ p. 34), physical startups and upsets cause the release—but human-wire latency hid 28 unreported events (9.6M lbs) in Lubbock until an audit uncovered them.*

**3. High latency hides massive physical releases.** When a pipeline ruptures (releasing 557,240 lbs of VOCs in Abilene) or a plant commissions new units (releasing 16.0M lbs in Corpus Christi), physical equipment is the direct cause—which is why direct wire failures represent only 5% to 10% of unauthorized pollutant mass (TCEQ p. 33). Yet look at TCEQ Region 2 (Lubbock) in that same report: a single company conducting an internal audit discovered 28 previously unreported emissions events totaling 9.6 million pounds that had gone unnoticed and unreported in the manual workflow. A slow, lossy wire does not crack the pipe—but it blinds the people who could have shut the valve.

## V. What Changed After 50 Years to Let Us Unwire Humans

*For half a century, three technical walls kept humans trapped in the middle of the loop. Over the past few years, all three walls fell at once.*

If using humans as wires is so wasteful, why did the 1970s compliance architecture survive for fifty years—and why can we suddenly replace it today? Because three foundational walls just collapsed:

### Wall 1: Semantics—silicon learned to read the law

For 50 years, software could read numbers in a table, but it could not read an 800-page Title V permit, a federal MACT rule, or an unstructured lab PDF. Today, frontier AI models read permits and agency dockets directly (EnviroAI Platform)—translating English prose into explicit data-capture, deterministic-math, and human-judgment tasks while citing the exact page and marking any unconfirmed value as "Unknown" (NIST AI 600-1).

### Wall 2: Telemetry—continuous sensing replaced clipboards

Connecting a fan, flare, or outfall used to require trenching conduit and custom PLC code—so plants relied on monthly clipboards or annual stack tests that violated the Nyquist sampling theorem (f_s ≥ 2f_max). Today, connected historians, validated CEMS/PEMS, and live satellite and ambient feeds (22M+ indexed records) stream continuous physical context in real time.

### Wall 3: Payback—dead filing cabinets became live control

In the 1970s system, compliance data sat in six-month-old binders where a measurement could only be used to apologize for yesterday's exceedance. When the same validated bits flow in real time, they do double duty: proving compliance while catching wasted fuel, steam leaks, and catalyst drift early enough to pay back the engineering investment.

## VI. From 80% Wire Work to 90% Human Judgment

*When we unwire humans from clerical data transport, we don't shrink the human role—we invert it from 80% wire work to 90% creative stewardship.*

What happens to environmental work when we replace the 1970s human-wire architecture with connected, source-cited systems? We do not hand industrial plants over to autonomous black boxes: software never signs a permit submittal, never guesses a missing measurement, and never overrides a human operator's safety authority (EnviroAI Platform; OSHA 29 CFR § 1910.333). Instead, we achieve a profound structural inversion in how human beings spend their working lives:

- **1970s–2020s legacy system (humans as the wire):** 80% moving data—collecting, copying, unit math, PDF checks, reports—and 20% thinking.
- **Connected environmental intelligence (humans unwired):** 10% system oversight and 90% freed for judgment, investigation, process design, and pollution prevention.

**Empirical benchmark (EnviroAI deployment record):** On EnviroAI's first industrial tool deployed at a global petrochemical facility, a 50-hour manual regulatory and engineering workflow collapsed to 3 hours—eliminating 94% of the clerical wire-work while preserving 100% human review and sign-off over every unconfirmed value and engineering decision.

Look at what that shift from 80% wire / 20% thinker to 10% oversight / 90% thinker means in practice. The 10% that remains connected to the compliance software is no longer mind-numbing clerical transcription; it is high-level epistemic oversight—auditing the exact permit citation the system linked, examining the values the system explicitly flagged as "Unknown," and exercising professional judgment before signing. And the 90% of human bandwidth that is liberated goes back where it always belonged: walking the plant, questioning whether a clamp-on sensor is a valid indicator or just a proxy, diagnosing why a biological treatment basin is losing efficiency, and stopping pollution in the physical world before a single chemical bond is broken.

> The human being is not an unfortunate obstacle between two systems. The human being is the reason the disconnected system worked at all. Connect what can be connected reliably. Automate what can be specified and validated. Escalate what remains uncertain. Keep people accountable for judgment. People should not spend their working lives carrying information between machines. They should use information to understand the world—and make it better.

## References & Primary Sources

**Neuroscience & human bandwidth:** J. Zheng & M. Meister, "The Unbearable Slowness of Being: Why do we live at 10 bits/s?" *Neuron* (2025) & Caltech Science Exchange; C. Coupé et al., "Comparable information rates across the human communicative niche (39.15 bits/s)," *Science Advances* 5(9): eaaw2594 (2019); F.A.C. Azevedo, S. Herculano-Houzel et al., "The Human Brain in Numbers (86B neurons, 20 W)," *J. Comp. Neurol.* (2009); and H. Zenil et al., Working Memory Compression (2015).

**Thermodynamics & environmental intelligence:** J. Anderson, [The Bond-Bit Ratio: Why Information Is at Least 240× Cheaper Than Force](/essays/bond-bit-ratio) (DOI: 10.5281/zenodo.20723029), [The Physics of Zero-Cost Stewardship](/essays/the-physics-of-zero-cost-stewardship), [The Intelligence Leverage Equation](/essays/intelligence-leverage-equation), and EnviroAI Platform & Deployment Benchmarks.

**Regulatory & governance records:** TCEQ, FY 2025 Annual Enforcement Report (SFR-126/25); U.S. EPA, 40 CFR Part 75, SDWA Compliance, NPDES SNC Initiative, ECHO DMR Guide, Next Generation Compliance; GAO-21-290; OSHA 29 CFR § 1910.333; and NIST AI 600-1.
