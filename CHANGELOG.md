## [docling-metrics-layout-v0.13.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-layout-v0.13.0) - 2026-04-24

### Feature

* Introduce the GriTS metric for Table Structure Recognition in docling-metrics-table ([#23](https://github.com/docling-project/docling-metrics/issues/23)) ([`942ccec`](https://github.com/docling-project/docling-metrics/commit/942ccec7bc6ded5d96f1e9b49b8dd7333be39193))
* **text:** Ensure that computation of BLEU can happen in parallel using the evaluate library. ([#20](https://github.com/docling-project/docling-metrics/issues/20)) ([`f32df51`](https://github.com/docling-project/docling-metrics/commit/f32df51e4def7dfa2b6df2396393caf692839fd9))
* Introduce the docling-metrics-layout package ([#12](https://github.com/docling-project/docling-metrics/issues/12)) ([`61c2fa1`](https://github.com/docling-project/docling-metrics/commit/61c2fa186998d208d43b21208da95c11bf0c0b26))
* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Improve the error handling for docling-metrics-text ([#18](https://github.com/docling-project/docling-metrics/issues/18)) ([`749e0a7`](https://github.com/docling-project/docling-metrics/commit/749e0a7edea15c951b8b481cd1e7249efe3df40b))
* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-table-v0.12.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-table-v0.12.0) - 2026-04-24

### Feature

* Introduce the GriTS metric for Table Structure Recognition in docling-metrics-table ([#23](https://github.com/docling-project/docling-metrics/issues/23)) ([`942ccec`](https://github.com/docling-project/docling-metrics/commit/942ccec7bc6ded5d96f1e9b49b8dd7333be39193))
* **text:** Ensure that computation of BLEU can happen in parallel using the evaluate library. ([#20](https://github.com/docling-project/docling-metrics/issues/20)) ([`f32df51`](https://github.com/docling-project/docling-metrics/commit/f32df51e4def7dfa2b6df2396393caf692839fd9))
* Introduce the docling-metrics-layout package ([#12](https://github.com/docling-project/docling-metrics/issues/12)) ([`61c2fa1`](https://github.com/docling-project/docling-metrics/commit/61c2fa186998d208d43b21208da95c11bf0c0b26))
* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Improve the error handling for docling-metrics-text ([#18](https://github.com/docling-project/docling-metrics/issues/18)) ([`749e0a7`](https://github.com/docling-project/docling-metrics/commit/749e0a7edea15c951b8b481cd1e7249efe3df40b))
* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-text-v0.11.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-text-v0.11.0) - 2026-04-24

### Feature

* Introduce the GriTS metric for Table Structure Recognition in docling-metrics-table ([#23](https://github.com/docling-project/docling-metrics/issues/23)) ([`942ccec`](https://github.com/docling-project/docling-metrics/commit/942ccec7bc6ded5d96f1e9b49b8dd7333be39193))
* **text:** Ensure that computation of BLEU can happen in parallel using the evaluate library. ([#20](https://github.com/docling-project/docling-metrics/issues/20)) ([`f32df51`](https://github.com/docling-project/docling-metrics/commit/f32df51e4def7dfa2b6df2396393caf692839fd9))
* Introduce the docling-metrics-layout package ([#12](https://github.com/docling-project/docling-metrics/issues/12)) ([`61c2fa1`](https://github.com/docling-project/docling-metrics/commit/61c2fa186998d208d43b21208da95c11bf0c0b26))
* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Improve the error handling for docling-metrics-text ([#18](https://github.com/docling-project/docling-metrics/issues/18)) ([`749e0a7`](https://github.com/docling-project/docling-metrics/commit/749e0a7edea15c951b8b481cd1e7249efe3df40b))
* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-chemistry-v0.10.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-chemistry-v0.10.0) - 2026-04-23

### Feature

* Introduce the GriTS metric for Table Structure Recognition in docling-metrics-table ([#23](https://github.com/docling-project/docling-metrics/issues/23)) ([`942ccec`](https://github.com/docling-project/docling-metrics/commit/942ccec7bc6ded5d96f1e9b49b8dd7333be39193))
* **text:** Ensure that computation of BLEU can happen in parallel using the evaluate library. ([#20](https://github.com/docling-project/docling-metrics/issues/20)) ([`f32df51`](https://github.com/docling-project/docling-metrics/commit/f32df51e4def7dfa2b6df2396393caf692839fd9))
* Introduce the docling-metrics-layout package ([#12](https://github.com/docling-project/docling-metrics/issues/12)) ([`61c2fa1`](https://github.com/docling-project/docling-metrics/commit/61c2fa186998d208d43b21208da95c11bf0c0b26))
* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Improve the error handling for docling-metrics-text ([#18](https://github.com/docling-project/docling-metrics/issues/18)) ([`749e0a7`](https://github.com/docling-project/docling-metrics/commit/749e0a7edea15c951b8b481cd1e7249efe3df40b))
* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-layout-v0.9.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-layout-v0.9.0) - 2026-02-25

### Feature

* Introduce the docling-metrics-layout package ([#12](https://github.com/docling-project/docling-metrics/issues/12)) ([`61c2fa1`](https://github.com/docling-project/docling-metrics/commit/61c2fa186998d208d43b21208da95c11bf0c0b26))
* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-text-v0.8.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-text-v0.8.0) - 2026-02-24

### Feature

* Optimized C++ implementation for edit_distance ([#14](https://github.com/docling-project/docling-metrics/issues/14)) ([`dfa27db`](https://github.com/docling-project/docling-metrics/commit/dfa27db7ae381d0c0832b0aec98b9df93288efe6))
* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-table-v0.7.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-table-v0.7.0) - 2026-02-17

### Feature

* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Pypi.yml missing uvx was silently failing in parsing pyproject.toml ([#13](https://github.com/docling-project/docling-metrics/issues/13)) ([`288567e`](https://github.com/docling-project/docling-metrics/commit/288567eec899edad10c80d718bf66a943a02244b))
* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-table-v0.6.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-table-v0.6.0) - 2026-02-16

### Feature

* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Rename docling-metrics-teds as docling-metrics-table ([#11](https://github.com/docling-project/docling-metrics/issues/11)) ([`d89dbf2`](https://github.com/docling-project/docling-metrics/commit/d89dbf2635474ae63a5e3bd95f43dac26b4ffa3a))
* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

### Documentation

* Update README.md for docling-metrics-text and docling-metrics-teds ([#10](https://github.com/docling-project/docling-metrics/issues/10)) ([`60c648c`](https://github.com/docling-project/docling-metrics/commit/60c648c46e21fc00b5f166daebf484a9f246ee29))

## [docling-metrics-text-v0.5.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-text-v0.5.0) - 2026-02-16

### Feature

* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

## [docling-metrics-text-v0.4.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-text-v0.4.0) - 2026-02-16

### Feature

* Introduce docling-metrics-text with implementations of text metrics ([#7](https://github.com/docling-project/docling-metrics/issues/7)) ([`68f8f58`](https://github.com/docling-project/docling-metrics/commit/68f8f58d29bcfca5be00551cede7414e225d2a6d))
* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

### Fix

* Fix the evaluate_sample() in BaseMetric to properly accept one BaseInputSample parameter ([#8](https://github.com/docling-project/docling-metrics/issues/8)) ([`87a8396`](https://github.com/docling-project/docling-metrics/commit/87a83964e0af4203a0ad29600ad3ade60424158e))

## [docling-metrics-teds-v0.3.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-teds-v0.3.0) - 2026-02-05

### Feature

* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

## [docling-metric-teds-v0.2.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metric-teds-v0.2.0) - 2026-02-05

### Feature

* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

## [docling-metrics-core-v0.1.0](https://github.com/docling-project/docling-metrics/releases/tag/docling-metrics-core-v0.1.0) - 2026-02-05

### Feature

* Introduce the docling-metric-teds project ([#2](https://github.com/docling-project/docling-metrics/issues/2)) ([`c7ab080`](https://github.com/docling-project/docling-metrics/commit/c7ab080e82f02a0a1cf0c145c3c974bdb1bc362c))
* Hello world metric example with C++ backend and pybind ([#4](https://github.com/docling-project/docling-metrics/issues/4)) ([`3409864`](https://github.com/docling-project/docling-metrics/commit/340986404ed6522a3479646f4f0045eec10072e3))
* Turn into monorepo ([`475a355`](https://github.com/docling-project/docling-metrics/commit/475a3554fa1b58e80d36653f864114dd55e36bc3))

