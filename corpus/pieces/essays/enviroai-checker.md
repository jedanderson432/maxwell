<!-- License: CC BY 4.0 (some pieces CC0). Reading, quoting in full, indexing, retrieval and training are permitted with attribution: Jed Anderson, jedanderson.org. -->
---
title: 'The EnviroAI Checker'
slug: 'enviroai-checker'
date: 2026-11-24
type: 'essay'
status: 'published'
tags: ['enviroai', 'ai', 'incorruptible-grader', 'monitoring', 'environmental-intelligence', 'accessible', 'visual-essay']
abstract: 'A 14-slide deck on how to trust AI work that no person can read. The Riemann proof ran 17 million lines and was still verified, because people wrote the claim beforehand and a small, readable program checked every step. The EnviroAI Checker is designed to carry that method into environmental work: people keep the aim, the test, and the measurements, and every number arrives with a receipt reading pass, fail, or not checked.'
license: 'CC-BY-4.0'
author: 'Jed Anderson'
co_authors: []
canonical_url: 'https://jedanderson.org/essays/enviroai-checker'
pdf: '/pdfs/enviroai-checker.pdf'
hero_image: '/images/enviroai-checker-hero.jpg'
hero_image_alt: 'Title cover reading ''The EnviroAI Checker'' in the site palette, with no other text.'
supporting_files: []
pdf_canonical: true
pdf_pages: 14
related_essay: '/essays/incorruptible-grader'
---

The news, as the deck opens: on November 20, 2026, AI helped prove the Riemann hypothesis, the most famous unsolved problem in mathematics. The bigger news is that no human can check it, and it was verified anyway. The proof runs 17 million lines. The written explanation runs past 250,000 pages. Machines checked every line in a day. How it was verified is the part that matters for environmental work.

## I. AI's Work Is Moving Past What People Can Read

The first sign came in March 2016, when an AI played a Go move no expert understood. By the AI maker's own data, there was a 1 in 10,000 chance a human would have played Move 37. Nobody had to understand the move to know it worked. The rules of the game decided. Understanding came later: human play had stayed level for 66 years, then improved once players could study the AI's moves.

Ten years on, the gap is wider. In September 2026, Navier-Stokes: 616,000 lines of proof. In November 2026, Riemann: 17 million lines, with no plain-language account yet.

The limit is the human brain, and more people do not remove it. At 10 seconds a line and 2,000 working hours a year, reading the Riemann proof once would take one person 24 years. Twelve expert referees spent four years on the far smaller Kepler conjecture proof and came away 99% sure. A person can hold about four things in mind at once. The human line is flat because the brain is fixed. If AI keeps improving at all, the gap widens.

## II. How Do You Trust Something No One Can Understand?

Not by trusting the AI. Other people had written the claim beforehand. A small, simple program checked every step, and separate groups ran their own. People cannot follow the proof. They can read the claim and the checker.

Until now, people trusted the work because other people could read it and follow it. From now, work no one can read or understand is trusted by testing it against a claim people wrote. People keep three things in their own hands:

- **The aim.** What we asked for, in plain words.
- **The test.** How we check it, small enough to read.
- **The measurements.** What the instruments say.

Nobody re-weighs every bag at the grocery store. An inspector certifies the scale. Then everyone trusts the weight. People stop checking the work. They check the checker.

## III. Five Ways to Trust AI's Work. Only One Scales.

1. **Stop using AI.** That would mean pulling the plug and outlawing AI everywhere. It is no longer a real option.
2. **Trust the AI.** It can be wrong, and it does not always know when.
3. **Have people review it.** The work is already past what people can read or understand.
4. **Have another AI grade it.** It can make the same mistake for the same reason.
5. **Build simple checkers.** Small tests that anyone can read and re-run. This is the one that scales, and it is how the Riemann proof earned trust.

## IV. What the EnviroAI Checker Is Designed to Do

To bridge human and machine understanding:

1. **Translate.** To turn work no one can read into pass, fail, or not checked.
2. **Anchor to the real world.** To test claims against measurements, not only paper.

The methods can pass beyond us. The aim, the test, and the evidence would stay ours.

To keep machine impact under human control:

3. **Stay outside the AI.** So the AI cannot change its checker or its monitors.
4. **Gate action.** So the AI acts only inside limits a check can confirm.
5. **Watch the outcome itself.** To measure the river, not only the report.
6. **Keep a small readable core.** Small enough to read, and re-runnable by anyone.

## V. How It Would Work

People write the claim. AI does the work. Instruments supply the measurements. The checker tests the work against the claim, and one of three things happens:

- **Pass.** It becomes a fact, with a receipt.
- **Fail.** It goes back with the reason.
- **Not checked.** A person is told.

People would keep the claim and the instruments. The AI could not change the claim, the checker, or the instruments.

A checker is a small test that runs automatically, every time. Its result would look like a receipt attached to a number. For the claim *Boiler 1 emitted 34 tons of NOx in 2025*, the receipt would read:

| Check | Result |
|---|---|
| Do the units work out? | PASS |
| Does the math give 34? | PASS |
| Is every number traced to a record? | PASS |
| Is the cited rule real and current? | PASS |
| Is the result physically possible? | PASS |
| Is it under the permit limit of 40? | PASS |
| Does it match the stack monitor? | NOT CHECKED |

6 passed · 0 failed · 1 not checked. “Not checked” would be shown, never hidden.

> **A number with a receipt is a fact. A number without one is a draft.**

## VI. Where This Is Heading

**Now.** AI drafts the work. People can still review it piece by piece. Volume is the strain.

**Heading.** AI writes the work and the tests, and starts to act. No one can say how fast. Navier-Stokes fell in September, Riemann in November.

**Holds regardless.** Measurement. Independence. A human aim. Human accountability. The checker's lasting job would be to hold these four.

People keep the aim, the test, and the measurements. Machines do the rest. We would like to design and build the EnviroAI Checker with you.

*The full deck, with its charts and diagrams, is in the canonical PDF above. The physical-world version of the same argument is in [Reality as the Only Incorruptible Grader](/essays/incorruptible-grader).*

## Sources

- Google DeepMind, “What we learned in Seoul with AlphaGo,” 2016.
- Shin and others, *PNAS*, 2023, on human play after AI.
- Cowan, 2001, on working memory.
- The Kepler conjecture proof and its refereeing, 1998 to 2003.
- The Riemann proof was released by mathematician Levent Alpöge, working with the AI model Claude, and was checked by machine and certified by the Lean and Mathlib communities. Mathematicians are still working to understand how it works.
- Reading time is our arithmetic. The widening-gap chart in the deck is an illustration, not a measurement; the three events on it are real.
