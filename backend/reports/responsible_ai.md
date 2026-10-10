# Responsible AI, Fairness, and Explainability Note
**Lloyds Megathon X — Problem Statement 2 (Section 13 H & Phase 15)**

---

## 1. Privacy and Data Governance
- **Zero Personal Identifiable Information (PII)**: The training and evaluation pipeline uses synthetic records representing housing stock archetypes without personal customer identifiers, bank account data, or precise street addresses.
- **Leakage Prevention**: All cross-validation and evaluation splits are partitioned strictly at the customer identifier level to prevent data leakage between properties owned by the same landlord.

---

## 2. Fairness and Non-Penalization of Size
- **Floor-Area Normalization**: Consumption intensity is evaluated in $\text{kWh}/\text{m}^2/\text{year}$. A larger family home with higher total aggregate consumption is **not unfairly penalized** as an inefficient home if its thermal envelope per unit of floor area is well insulated.
- **Regional Equity**: Property valuation models evaluate relative percentage ranges rather than raw absolute values, preventing regional price disparities (e.g., London vs North East) from distorting retrofit suitability recommendations.

---

## 3. Explainability and Transparency
- **Deterministic Scoring**: The Green Home Score is computed via transparent, documented weights and monotonic piecewise mappings. Machine learning is not used to replace this deterministic formulation.
- **Seven Component Breakdowns**: Every score output provides raw sub-scores, fixed percentage weights, weighted numerical contributions, and explicit narrative explanations for each component.
- **Transparent Interactions**: Recommendations show the difference between naive standalone summation and true sequential physical interactions (highlighting interaction discounts and heat pump electricity trade-offs).

---

## 4. Hallucination Prevention and Grounded AI
- **Strict Grounding Guardrails**: The GenAI explanation layer strictly consumes numbers pre-computed by the deterministic calculation engines.
- **Anti-Hallucination Constraints**: The LLM is prohibited from calculating scores or inventing energy/carbon savings. Groundedness targets are $\ge 90\%$, factual accuracy $\ge 90\%$, and unsupported claims $< 5\%$.
- **Offline Deterministic Fallback**: When external LLM APIs are unreachable or unset, a deterministic template engine produces fully grounded explanations without network dependencies.

---

## 5. Human Oversight and Causal Caveats
- **Surveyor Disclaimer**: All energy savings and carbon reductions are presented as indicative modelled estimates, not formal engineering guarantees.
- **Valuation Disclaimer**: Property value impacts are presented as indicative observational ranges, accompanied by clear warnings that observational market correlations do not constitute a formal RICS Red Book valuation or guaranteed market increase.
