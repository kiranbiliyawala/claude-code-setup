# Archana PR Review Plan

## Objective
Review 27 PRs submitted by Archana across 5 repositories and evaluate their coding skills against Google's L3 backend engineering bar.

## PRs to Review (27 total)

### Payment Service (17 PRs)
| PR # | Description |
|------|-------------|
| 832 | CVV disablement support at provider level |
| 891 | Digio sync flow fix with redirection parameters |
| 900 | Settlement route integration for digio provider |
| 917 | Enriching RRN for rzp mandate provider |
| 944 | ICICI UPI provider prefix fix |
| 1037 | Mandate token enrichment on failed payment attempt |
| 1041 | Wallet stuck in CREATE state fix |
| 1047 | Digio refund integration |
| 1059 | Token type support to LCM resolve terminal |
| 1077 | Cashback wallet utilisation in autopay registration |
| 1103 | Refund adjustment backfill API |
| 1118 | Billdesk 404 handling in refund flow |
| 1131 | Guest checkout flow fix (compliance) |
| 1141 | HB Darwin DT UI fix - cache in global config |
| 1170 | Razorpay refund sync fallback on payment id |
| 1191 | Non-2xx handling for billdesk |
| 1213 | Inline autopay refund support |

### MPO (2 PRs)
| PR # | Description |
|------|-------------|
| 190 | PPI authentication support |
| 196 | PPI debit call error msg handling |

### Loading Capability Manager (3 PRs)
| PR # | Description |
|------|-------------|
| 192 | Preference maker checker and reserved udf contract fix |
| 221 | Token type support for resolve terminal flow |
| 223 | Cashback wallet support for mandate with pay flow |

### Mandate Service (3 PRs)
| PR # | Description |
|------|-------------|
| 110 | UPI mandate revoke flow support |
| 112 | UPI mandate pause webhook integration |
| 115 | Duplicate axis webhook fix |

### Genie (2 PRs)
| PR # | Description |
|------|-------------|
| 682 | Handling UTR-22 |
| 645 | Balance check APIs |

## Execution Plan

### Step 1: Review Each PR
For each PR, I will:
1. Fetch the PR diff using `gh pr diff`
2. Analyze code changes for:
   - Code quality and readability
   - Error handling
   - Edge cases coverage
   - Design patterns and modularity
   - Language/framework expertise
   - Testing approach
   - Security considerations

### Step 2: Create Individual Summary Files
Create a summary file for each PR in `/Users/kiranbiliyawala/code/cred/payments/archana/reviews/`:
- `pr-832-summary.md`, `pr-891-summary.md`, etc.

### Step 3: Create Overall Feedback File
Compile all reviews into `archana-overall-feedback.md` with:

## Evaluation Dimensions
1. **Modularity** - Code organization, separation of concerns, reusability
2. **Code Quality** - Readability, naming conventions, clean code practices
3. **Language Expertise** - Kotlin/Java proficiency, idiomatic code
4. **Error Handling** - Robustness, edge cases, failure modes
5. **Design Patterns** - Use of appropriate patterns, architecture decisions
6. **Testing** - Test coverage, test quality
7. **Security Awareness** - Security considerations in payment flows
8. **Problem Solving** - Approach to fixing bugs and implementing features

## L3 Backend Engineer Bar (Google)
An L3 engineer at Google should demonstrate:
- Independent implementation of well-defined features
- Good understanding of data structures and algorithms
- Clean, readable, maintainable code
- Appropriate error handling and testing
- Basic system design understanding
- Ability to debug and fix issues

## Output Files
- `reviews/` directory with individual PR summaries
- `archana-overall-feedback.md` with comprehensive evaluation

## Verification
- All PR diffs fetched successfully
- Individual summaries created for each PR
- Overall feedback includes L3 evaluation and dimensional ratings
