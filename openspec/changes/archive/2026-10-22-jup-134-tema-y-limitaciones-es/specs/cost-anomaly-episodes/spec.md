## MODIFIED Requirements

### Requirement: Versioned rules and honest limitations

Each episode SHALL store the rules version and thresholds that opened it; runs SHALL only use the current business rules. Episodes SHALL be presented as candidates: the system SHALL NOT claim a cause, savings, statistical confidence or completeness of the cost data. Documented limitations SHALL include: a day may be evaluated before late data arrives; a service with no earlier spend does not open an episode on its first day, but from its second day the reference is the seven-day mean including that first day, so steady new spend can open an episode and escalate until someone closes it; weekly cycles may produce false candidates; a recent spike raises the seven-day mean; currencies other than EUR and USD are not evaluated; only the service dimension is watched. The limitations returned with each episode SHALL be written in Spanish, keeping the same five statements in the same order, and SHALL be the same list that the anomaly explanation in the assistant presents.

#### Scenario: Rules recorded on the episode
- **WHEN** an episode is opened
- **THEN** it stores the rules version together with 20 %, 100.00, seven reference days, three tolerance days and the severity tiers

#### Scenario: Limitations exposed
- **WHEN** any episode is read
- **THEN** the response includes cause_status not_established and the limitations list

#### Scenario: Limitations in Spanish
- **WHEN** any episode is read
- **THEN** its limitations list has five statements written in Spanish, starting with «Es un candidato para investigar, no una causa demostrada, un ahorro ni una confianza estadística.»
- **AND** none of them is the previous English wording, such as «A candidate for investigation, not a demonstrated cause, saving or statistical confidence.»

#### Scenario: Same limitations in the panel and in the assistant
- **WHEN** an episode is read and the same episode is explained in the assistant
- **THEN** the episode limitations and the limitations of the explanation are the same statements in the same order
