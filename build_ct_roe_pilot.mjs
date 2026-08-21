import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const PROJECT_ROOT = process.cwd();
const OUTPUT_DIR = path.join(PROJECT_ROOT, "outputs", "roe_pilot_2013_2024");
const PREVIEW_DIR = path.join(PROJECT_ROOT, "tmp", "roe-workbook", "previews");
const PROCESSED_DIR = path.join(PROJECT_ROOT, "data", "processed");
const RETRIEVED_DATE = "2026-08-09";

const SOURCE_URLS = {
  S01: "https://portal.ct.gov/-/media/ag/press_releases/2013/20130718agaquarionbriefpdf.pdf?hash=B1B061A8844E85A94AFD8C7ACD66E3D1&rev=1f870b7d8f724e82bc16769894cdfad1",
  S02: "https://portal.ct.gov/occ/-/media/occ/121714pressreleaseonclpfinaldecision1pdf.pdf?hash=F7B808F81767627F1C5DF35E15F23070&rev=800013e1dc584a4896605fd6e0d51c32",
  S03: "https://www.sec.gov/Archives/edgar/data/13372/000007274117000007/a201610kdocument.htm",
  S04: "https://www.sec.gov/Archives/edgar/data/72741/000007274118000042/a2018q110-qxdocument.htm",
  S05: "https://portal.ct.gov/pura/industries/rates",
  S06: "https://portal.ct.gov/pura/press-releases/2021/pura-issues-final-decision-in-docket-number-20-08-03",
  S07: "https://www.sec.gov/Archives/edgar/data/1082510/000114036115009017/form10k.htm",
  S08: "https://portal.ct.gov/pura/docket/final-decision-database",
  S09: "https://portal.ct.gov/-/media/occ/4272023-occ-brief.pdf",
  S10: "https://d2f1dfnoetc03v.cloudfront.net/Files/Misplaced-Files-Cleanup/220808-082523.pdf",
  S11: "https://portal.ct.gov/pura/press-releases/2023/pura-ruling-sets-distribution-rates-for-united-illuminating-customers?archived=true",
  S12: "https://www.sec.gov/Archives/edgar/data/1634997/000119312515407879/d105528d8k.htm",
  S13: "https://www.avangrid.com/aboutus/companyprofile",
  S14: "https://investors.eversource.com/static-files/1526fda9-4ffa-4cfd-bbd7-c9c18f56d3fe",
  S15: "https://portal.ct.gov/-/media/AG/Press_Releases/2023/22-08-08_AG-Brief_Final-42723.pdf",
  S16: "https://portal.ct.gov/-/media/AG/Press_Releases/2019/AG-Brief_Docket-No-20-08-03_020521.pdf",
  S17: "https://www.sec.gov/Archives/edgar/data/1634997/000163499718000029/avangrid2018q310-q.htm",
  S18: "https://www.mass.gov/doc/dpu-17-05/download",
  S19: "https://www.sec.gov/Archives/edgar/data/13372/000110465923036619/tm231858d6_ars.pdf",
  S20: "https://www.mass.gov/doc/dpu-annual-report-2022/download",
  S21: "https://www.nationalgrid.com/document/138981/download",
  S22: "https://www.mass.gov/doc/grid-elec-rate-case-dpu-15-155/download",
  S23: "https://www.sec.gov/Archives/edgar/data/1004315/000119312516765037/d291640dex991.htm",
  S24: "https://www.sec.gov/Archives/edgar/data/1004315/000100431519000140/resultsstatementhy201920.htm",
  S25: "https://www.mass.gov/doc/final-recommendations-from-the-financing-the-transition-focus-area-work-group/download",
  S26: "https://www.mass.gov/info-details/dpu-23-150-national-grid-electric-base-distribution-rate-case",
  S27: "https://www.sec.gov/Archives/edgar/data/72741/000007274118000028/a201710kdocument.htm",
  S28: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B1714A09D-088F-4343-BF91-8DEA3685A614%7D",
  S29: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B2148C1DE-E631-4E81-A447-C8E7E11EC6D9%7D",
  S30: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B77923784-556A-47A6-B2CC-19F5C252C966%7D",
  S31: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B7B06921C-6160-4FFD-B10F-1C1D03F16AEE%7D",
  S32: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B40057589-0000-CA12-8AED-981944A08EED%7D",
  S33: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B4CF18507-1968-4E38-9DB6-FD33FAF8426F%7D",
  S34: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B9DD1BECA-915E-427E-A430-CC771B9EDE7C%7D",
  S35: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B4E457600-A932-4843-9EBA-CEEE6CAA6457%7D",
  S36: "https://documents.dps.ny.gov/public/Common/ViewDoc.aspx?DocRefId=%7B508D258B-0000-C11C-A3DC-C20B65EE38E7%7D",
  S37: "https://investor.conedison.com/static-files/0b4e12b3-f43b-4398-a04b-3699537cabb5",
};

const sources = [
  ["S01", "Connecticut Office of the Attorney General", "Post-hearing brief citing then-current authorized ROEs", "2013-07-18", SOURCE_URLS.S01, "p. 4", "CL&P 9.40%; UI 8.75% before its 2013 decision", "Official state filing; used only for the stated carried-in ROEs"],
  ["S02", "Connecticut Office of Consumer Counsel", "CL&P final rate decision press release", "2014-12-17", SOURCE_URLS.S02, "pp. 1-2", "CL&P 9.17% base ROE; approximately $134 million approved increase; one-year penalty described", "Official state consumer advocate summary of PURA decision"],
  ["S03", "The Connecticut Light and Power Company / SEC", "2016 Form 10-K", "2017-02-28", SOURCE_URLS.S03, "Distribution rate case discussion", "2014 decision effective 2014-12-01; 2015 one-year ROE reduction ended for 2016", "Company filing with the U.S. Securities and Exchange Commission"],
  ["S04", "Eversource Energy / SEC", "Quarterly report for the quarter ended March 31, 2018", "2018-05-03", SOURCE_URLS.S04, "Connecticut rate case discussion", "Settlement approved 2018-04-18; 9.25% ROE; 53% equity; $64.3m/$31.1m/$29.2m rate steps", "Company filing with the U.S. Securities and Exchange Commission"],
  ["S05", "Connecticut Public Utilities Regulatory Authority", "Current electric rate-case information", RETRIEVED_DATE, SOURCE_URLS.S05, "Electric distribution company table", "Most recent completed cases listed as CL&P 17-10-46 and UI 22-08-08", "Official regulator webpage; used to check for a later completed case"],
  ["S06", "Connecticut Public Utilities Regulatory Authority", "Final decision in Docket 20-08-03 (Tropical Storm Isaias)", "2021-04-27", SOURCE_URLS.S06, "Press release summary", "Future-proceeding ROE adjustments of 90 bp for Eversource and 15 bp for UI", "Official regulator source; order did not itself replace the in-force annual ROE"],
  ["S07", "UIL Holdings / SEC", "2014 Form 10-K", "2015-02-27", SOURCE_URLS.S07, "UI distribution rate case discussion", "August 2013 UI decision; ROE increased from 8.75% to 9.15%", "Company filing with the U.S. Securities and Exchange Commission"],
  ["S08", "Connecticut Public Utilities Regulatory Authority", "Final Decision database entry for Docket 16-06-04", "2016-12-14", SOURCE_URLS.S08, "Search Docket 16-06-04; decision tables and conclusion", "UI 2017-2019 rate base, revenue requirements, and rate changes", "Official PURA database; the former company-hosted direct PDF returned 404 on 2026-08-10"],
  ["S09", "Connecticut Office of Consumer Counsel", "Brief in Docket 22-08-08", "2023-04-27", SOURCE_URLS.S09, "pp. 7-8", "UI actual earned ROE, 2017-2021", "Official state consumer advocate filing"],
  ["S10", "Connecticut Public Utilities Regulatory Authority", "Final Decision, Docket 22-08-08", "2023-08-25", SOURCE_URLS.S10, "Tables 1 and 80; ROE discussion", "UI 9.10% base ROE, 47 bp total adjustment, 8.63% effective ROE, 50% equity, $1,105.196m rate base, $384.865m revenue requirement", "Controlling final decision used where proposed-final materials differed"],
  ["S11", "Connecticut Public Utilities Regulatory Authority", "PURA ruling sets distribution rates for UI customers", "2023-08-25", SOURCE_URLS.S11, "Press release summary", "About 6.6% base-distribution increase and about 2% overall-bill increase", "Official regulator summary; used as a plain-language cross-check"],
  ["S12", "Avangrid / SEC", "Form 8-K reporting completion of Iberdrola-USA / UIL combination", "2015-12-17", SOURCE_URLS.S12, "Item 2.01", "Ownership change underlying UI's MTC coding from 2016", "Company filing with the U.S. Securities and Exchange Commission"],
  ["S13", "Avangrid", "Company profile", RETRIEVED_DATE, SOURCE_URLS.S13, "Company overview", "Avangrid relationship to the Iberdrola group", "Official company source used with the SEC merger filing"],
  ["S14", "Eversource Energy", "Eversource ownership source used in project crosswalk", RETRIEVED_DATE, SOURCE_URLS.S14, "Corporate document", "Domestic parent evidence for CL&P / Eversource Connecticut", "Official company source"],
  ["S15", "Connecticut Office of the Attorney General", "Final brief in Docket 22-08-08", "2023-04-27", SOURCE_URLS.S15, "Capital structure and comparison discussion", "UI's 2013-approved 50% equity ratio; CL&P 9.25% current authorized ROE at filing", "Official state filing; not used for the final 2023 UI penalty because the later final decision controls"],
  ["S16", "Connecticut Office of the Attorney General", "Brief in Docket 20-08-03 discussing prior performance penalties", "2021-02-05", SOURCE_URLS.S16, "Discussion of the 2014 CL&P rate decision", "Exact 15 bp one-year CL&P storm-response adjustment", "Official state filing used to verify the exact basis-point adjustment"],
  ["S17", "Avangrid / SEC", "Quarterly report for the quarter ended September 30, 2018", "2018-09-30", SOURCE_URLS.S17, "UI rate-plan discussion", "2016 PURA decision effective 2017; 9.10% ROE and 50% equity ratio", "Stable SEC-filed corroboration used as the primary website link for the 2017-2022 ROE"],
  ["S18", "Massachusetts Department of Public Utilities", "Final Order, D.P.U. 17-05", "2017-11-30", SOURCE_URLS.S18, "pp. 713-714 and schedules 1 and 3", "NSTAR carried-in 10.50% ROE; approved 10.00% ROE, 53.34% equity ratio, and $2,732.852m rate base", "Official regulator final order; SEC filing S27 supplies the compliance-rate effective date"],
  ["S19", "Eversource Energy / SEC", "2022 Annual Report", "2023-03-24", SOURCE_URLS.S19, "Massachusetts distribution rate-case discussion", "D.P.U. 22-22 approved 9.80% ROE, 53.2% equity ratio, and a $64m base-distribution increase", "Company annual report filed with the U.S. Securities and Exchange Commission"],
  ["S20", "Massachusetts Department of Public Utilities", "2022 Annual Report", "2023", SOURCE_URLS.S20, "Electric distribution rate-case summary", "D.P.U. 22-22 decision date and 2023-01-01 effective date", "Official regulator cross-check for timing of the NSTAR decision"],
  ["S21", "National Grid", "Annual Report and Accounts 2015/16", "2016", SOURCE_URLS.S21, "US regulated returns table", "Massachusetts Electric 10.35% allowed ROE and 50:50 equity-to-debt ratio before D.P.U. 15-155", "Official company annual report; used for the carried-in 2013-2015 rate"],
  ["S22", "Massachusetts Department of Public Utilities", "Final Order, D.P.U. 15-155", "2016-09-30", SOURCE_URLS.S22, "Introduction and company description", "Prior D.P.U. 09-39 rate plan, 2016 effective timing, and National Grid plc parent incorporated in England and Wales", "Official regulator final order; also supports MTC ownership coding"],
  ["S23", "National Grid / SEC", "Half-year results, 2016/17", "2016-11-10", SOURCE_URLS.S23, "Massachusetts rate-case summary", "D.P.U. 15-155 approved 9.90% ROE, 51% equity ratio, and $101m annual revenue increase", "Company results filed with the U.S. Securities and Exchange Commission"],
  ["S24", "National Grid / SEC", "Half-year results, 2019/20", "2019-11-14", SOURCE_URLS.S24, "Massachusetts Electric rate-case summary", "D.P.U. 18-150 approved 9.60% ROE, 53.5% equity ratio, and $42m initial annual revenue increase", "Company results filed with the U.S. Securities and Exchange Commission"],
  ["S25", "Massachusetts Department of Public Utilities", "Financing the Transition work-group final recommendations", "2025-06-30", SOURCE_URLS.S25, "p. 6, table of recently authorized ROEs", "D.P.U. 23-150 approved 9.35% ROE and 52.83% equity ratio for Massachusetts Electric", "Official regulator document summarizing the final order's capital parameters"],
  ["S26", "Massachusetts Department of Public Utilities", "D.P.U. 23-150 National Grid electric base distribution rate case", RETRIEVED_DATE, SOURCE_URLS.S26, "Case overview and key dates", "Final-order date and November 2024 customer-bill timing", "Official regulator case page used to cross-check the 2024 timing"],
  ["S27", "Eversource Energy / SEC", "2017 Form 10-K", "2018-02-22", SOURCE_URLS.S27, "NSTAR Electric distribution rate-case discussion", "D.P.U. 17-05 decision issued 2017-11-30; new rates took effect 2018-02-01 after the compliance filing; 10.00% ROE", "Company filing with the U.S. Securities and Exchange Commission used to verify effective timing"],
  ["S28", "New York Public Service Commission", "Order Approving Electric, Gas, and Steam Rate Plans in Accord with Joint Proposal", "2014-02-21", SOURCE_URLS.S28, "p. 23 (PDF p. 26)", "Con Edison electric ROE changed from 10.15% to 9.20% for 2014-2015", "Official regulator final order"],
  ["S29", "New York Public Service Commission", "Order Adopting Terms of Joint Proposal to Extend Electric Rate Plan", "2015-06-17", SOURCE_URLS.S29, "p. 6 (PDF p. 9)", "Con Edison electric ROE changed from 9.20% to 9.00% for 2016", "Official regulator final order"],
  ["S30", "New York Public Service Commission", "Order Approving Electric and Gas Rate Plans", "2017-01-25", SOURCE_URLS.S30, "p. 26 (PDF p. 30)", "Con Edison 9.00% electric ROE for 2017-2019", "Official regulator final order"],
  ["S31", "New York Public Service Commission", "Order Adopting Terms of Joint Proposal and Establishing Electric and Gas Rate Plan", "2020-01-16", SOURCE_URLS.S31, "p. 23 (PDF p. 28)", "Con Edison 8.80% electric ROE for 2020-2022", "Official regulator final order"],
  ["S32", "New York Public Service Commission", "Order Adopting Terms of Joint Proposal and Establishing Electric and Gas Rate Plans with Additional Requirements", "2023-07-20", SOURCE_URLS.S32, "p. 17 (PDF p. 20)", "Con Edison 9.25% electric ROE for 2023-2025", "Official regulator final order"],
  ["S33", "New York Public Service Commission", "Order Establishing Rate Plan for NYSEG and RG&E", "2010-09-21", SOURCE_URLS.S33, "p. 34 (PDF p. 36)", "NYSEG 10.00% electric ROE carried into the pilot", "Official regulator final order"],
  ["S34", "New York Public Service Commission", "Order Approving Electric and Gas Rate Plans in Accord with Joint Proposal", "2016-06-15", SOURCE_URLS.S34, "p. 32 (PDF p. 35)", "NYSEG 9.00% electric ROE for the 2016-2019 rate plan", "Official regulator final order"],
  ["S35", "New York Public Service Commission", "Order Approving Electric and Gas Rate Plans in Accord with Joint Proposal, with Modifications", "2020-11-19", SOURCE_URLS.S35, "p. 62 (PDF p. 65)", "NYSEG 8.80% electric ROE for 2020-2022", "Official regulator final order"],
  ["S36", "New York Public Service Commission", "Order Adopting Joint Proposal", "2023-10-12", SOURCE_URLS.S36, "p. 27 (PDF p. 29)", "NYSEG 9.20% electric ROE for 2023-2026", "Official regulator final order"],
  ["S37", "Consolidated Edison, Inc.", "Con Edison ownership source used in project crosswalk", RETRIEVED_DATE, SOURCE_URLS.S37, "Corporate report", "Domestic parent evidence for Consolidated Edison Company of New York", "Official company source"],
];

const ownershipRows = [
  [4176, "Connecticut Light & Power Co", 2013, 2024, "DOM", "Eversource Energy", "United States", "S14", "DOM throughout the pilot"],
  [19497, "United Illuminating Co", 2013, 2015, "DOM", "UIL Holdings", "United States", "S12", "Pre-merger years remain DOM"],
  [19497, "United Illuminating Co", 2016, 2024, "MTC", "Iberdrola group through Avangrid", "Spain / multinational", "S12; S13", "Project assigns the completed December 2015 ownership change from calendar 2016"],
  [54913, "NSTAR Electric Company", 2013, 2024, "DOM", "Eversource Energy", "United States", "S14", "DOM throughout the pilot"],
  [11804, "Massachusetts Electric Company", 2013, 2024, "MTC", "National Grid plc", "United Kingdom / multinational", "S22", "Official DPU order identifies National Grid plc, incorporated in England and Wales, as the ultimate parent"],
  [4226, "Consolidated Edison Co-NY Inc", 2013, 2024, "DOM", "Consolidated Edison, Inc.", "United States", "S37", "DOM throughout the pilot"],
  [13511, "New York State Elec & Gas Corp", 2013, 2024, "MTC", "Iberdrola group through Avangrid", "Spain / multinational", "S13", "MTC throughout the pilot"],
];

const uiActualRoe = new Map([
  [2017, 0.0934],
  [2018, 0.0959],
  [2019, 0.1012],
  [2020, 0.0899],
  [2021, 0.0823],
]);

const uiDecisionInputs = new Map([
  [2017, { rateBase: 981.000, revenueRequirement: 363.034, revenueChange: 43.0 }],
  [2018, { rateBase: 997.026, revenueRequirement: 374.529, revenueChange: 11.5 }],
  [2019, { rateBase: 1014.144, revenueRequirement: 377.447, revenueChange: 3.0 }],
  [2023, { rateBase: 1105.196, revenueRequirement: 384.865, revenueChange: 22.957 }],
]);

function clpRow(year) {
  let baseRoe;
  let adjustmentBps = null;
  let equityRatio = null;
  let rateBase = null;
  let revenueRequirement = null;
  let revenueChange = null;
  let docket;
  let sourceIds;
  let annualizationNote;
  let sourceStatus;

  if (year === 2013) {
    baseRoe = 0.0940;
    docket = "09-12-05";
    sourceIds = "S01";
    sourceStatus = "Reported carried-in rate";
    annualizationNote = "Authorized ROE in force at the start of the pilot; exact rate base and equity ratio not collected in this step.";
  } else if (year <= 2017) {
    baseRoe = 0.0917;
    adjustmentBps = year === 2015 ? -15 : null;
    docket = "14-05-06";
    sourceIds = year === 2015 ? "S02; S03; S16" : "S02";
    sourceStatus = year === 2014 ? "Reported decision-year rate" : "Reported and carried forward";
    annualizationNote = year === 2014
      ? "Decision was effective 2014-12-01; the table records the rate in force at year-end."
      : year === 2015
        ? "One-year 15 bp storm-response reduction applied during 2015; base ROE remained 9.17%."
        : "9.17% base ROE carried forward after the one-year 2015 reduction ended.";
    if (year === 2014) revenueChange = 134.0;
  } else {
    baseRoe = 0.0925;
    equityRatio = 0.53;
    docket = "17-10-46";
    sourceIds = year >= 2022 ? "S04; S05" : "S04";
    sourceStatus = year === 2018 ? "Reported decision-year rate" : "Reported and carried forward";
    annualizationNote = year === 2018
      ? "Settlement approved 2018-04-18; first rate step effective 2018-05-01."
      : year === 2021
        ? "PURA separately ordered a 90 bp reduction for a future rate proceeding; it is not subtracted from this in-force annual series."
        : "Carried forward from the 2018 settlement; PURA's current rate-case page lists no later completed CL&P distribution rate case through this review.";
    if (year === 2018) revenueChange = 64.3;
    if (year === 2019) revenueChange = 31.1;
    if (year === 2020) revenueChange = 29.2;
  }

  return {
    utilityId: 4176,
    utilityName: "Connecticut Light & Power Co",
    displayName: "Eversource Connecticut (CL&P)",
    state: "CT",
    year,
    ownership: "DOM",
    baseRoe,
    adjustmentBps,
    actualRoe: null,
    equityRatio,
    rateBase,
    revenueRequirement,
    revenueChange,
    docket,
    sourceIds,
    actualSourceIds: null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: "S14",
  };
}

function uiRow(year) {
  let baseRoe;
  let adjustmentBps = null;
  let equityRatio;
  let docket;
  let sourceIds;
  let annualizationNote;
  let sourceStatus;

  if (year <= 2016) {
    baseRoe = 0.0915;
    equityRatio = 0.50;
    docket = "13-01-19";
    sourceIds = "S07; S15";
    sourceStatus = year === 2013 ? "Reported decision-year rate" : "Reported and carried forward";
    annualizationNote = year === 2013
      ? "August 2013 decision raised authorized ROE from 8.75% to 9.15%; the table records the rate in force at year-end."
      : year === 2016
        ? "9.15% remained in force through 2016; MTC coding begins in 2016 after the December 2015 merger."
        : "9.15% carried forward from the 2013 decision.";
  } else if (year <= 2022) {
    baseRoe = 0.0910;
    equityRatio = 0.50;
    docket = "16-06-04";
    sourceIds = "S17; S08";
    sourceStatus = year === 2017 ? "Reported decision-year rate" : "Reported and carried forward";
    annualizationNote = year === 2021
      ? "PURA separately ordered a 15 bp reduction for a future rate proceeding; it is not subtracted from this in-force annual series."
      : year <= 2019
        ? "Decision-year figures are attached only to the specific 2017-2019 rate year reported in the decision."
        : "9.10% carried forward from the 2016 decision; decision-year dollar inputs are not silently carried into later years.";
  } else {
    baseRoe = 0.0910;
    adjustmentBps = -47;
    equityRatio = 0.50;
    docket = "22-08-08";
    sourceIds = "S10; S11";
    sourceStatus = year === 2023 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2023
      ? "Final decision effective 2023-09-01: 9.10% base ROE less 47 bp of combined adjustments equals 8.63%."
      : "8.63% effective ROE carried forward from the final 2023 decision. Dollar inputs remain attached to the 2023 rate-year row only.";
  }

  const decisionInputs = uiDecisionInputs.get(year) ?? {};
  return {
    utilityId: 19497,
    utilityName: "United Illuminating Co",
    displayName: "United Illuminating",
    state: "CT",
    year,
    ownership: year <= 2015 ? "DOM" : "MTC",
    baseRoe,
    adjustmentBps,
    actualRoe: uiActualRoe.get(year) ?? null,
    equityRatio,
    rateBase: decisionInputs.rateBase ?? null,
    revenueRequirement: decisionInputs.revenueRequirement ?? null,
    revenueChange: decisionInputs.revenueChange ?? null,
    docket,
    sourceIds,
    actualSourceIds: uiActualRoe.has(year) ? "S09" : null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: year <= 2015 ? "S12" : "S12; S13",
  };
}

function nstarRow(year) {
  let baseRoe;
  let equityRatio = null;
  let rateBase = null;
  let revenueChange = null;
  let docket;
  let sourceIds;
  let sourceStatus;
  let annualizationNote;

  if (year <= 2017) {
    baseRoe = 0.1050;
    docket = "D.T.E. 05-85";
    sourceIds = "S18";
    sourceStatus = "Reported carried-in rate";
    annualizationNote = "D.P.U. 17-05 identifies 10.50% as NSTAR's then-current allowed ROE; the older case is not otherwise reconstructed here.";
  } else if (year <= 2022) {
    baseRoe = 0.1000;
    equityRatio = 0.5334;
    docket = "D.P.U. 17-05";
    sourceIds = year === 2018 ? "S18; S27" : "S18";
    sourceStatus = year === 2018 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2018
      ? "Final order set a 10.00% ROE; new rates took effect 2018-02-01 after the compliance filing. Decision-year rate base is stored only on this row."
      : "10.00% carried forward from D.P.U. 17-05 until the next base-rate decision took effect.";
    if (year === 2018) rateBase = 2732.851801;
  } else {
    baseRoe = 0.0980;
    equityRatio = 0.532;
    docket = "D.P.U. 22-22";
    sourceIds = "S19; S20";
    sourceStatus = year === 2023 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2023
      ? "D.P.U. 22-22 took effect 2023-01-01 with a 9.80% ROE and 53.2% equity ratio."
      : "9.80% carried forward from D.P.U. 22-22; no later completed NSTAR base-rate case was identified in this review.";
    if (year === 2023) revenueChange = 64.0;
  }

  return {
    utilityId: 54913,
    utilityName: "NSTAR Electric Company",
    displayName: "NSTAR Electric (Eversource Massachusetts)",
    state: "MA",
    year,
    ownership: "DOM",
    baseRoe,
    adjustmentBps: null,
    actualRoe: null,
    equityRatio,
    rateBase,
    revenueRequirement: null,
    revenueChange,
    docket,
    sourceIds,
    actualSourceIds: null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: "S14",
  };
}

function mecoRow(year) {
  let baseRoe;
  let equityRatio;
  let revenueChange = null;
  let docket;
  let sourceIds;
  let sourceStatus;
  let annualizationNote;

  if (year <= 2015) {
    baseRoe = 0.1035;
    equityRatio = 0.50;
    docket = "D.P.U. 09-39";
    sourceIds = "S21; S22";
    sourceStatus = "Reported carried-in rate";
    annualizationNote = "National Grid's 2015/16 annual report lists a 10.35% allowed ROE and 50:50 capital structure before the 2016 decision.";
  } else if (year <= 2018) {
    baseRoe = 0.0990;
    equityRatio = 0.51;
    docket = "D.P.U. 15-155";
    sourceIds = "S23; S22";
    sourceStatus = year === 2016 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2016
      ? "Final order took effect 2016-10-01; the table records the 9.90% rate in force at year-end."
      : "9.90% carried forward from D.P.U. 15-155.";
    if (year === 2016) revenueChange = 101.0;
  } else if (year <= 2023) {
    baseRoe = 0.0960;
    equityRatio = 0.535;
    docket = "D.P.U. 18-150";
    sourceIds = "S24";
    sourceStatus = year === 2019 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2019
      ? "Final order took effect 2019-10-01; the table records the 9.60% rate in force at year-end."
      : "9.60% carried forward from the five-year D.P.U. 18-150 rate plan.";
    if (year === 2019) revenueChange = 42.0;
  } else {
    baseRoe = 0.0935;
    equityRatio = 0.5283;
    docket = "D.P.U. 23-150";
    sourceIds = "S25; S26";
    sourceStatus = "Reported final decision";
    annualizationNote = "Final order was issued 2024-09-30 and reflected in customer bills beginning November 2024; the table records the year-end rate.";
  }

  return {
    utilityId: 11804,
    utilityName: "Massachusetts Electric Company",
    displayName: "Massachusetts Electric (National Grid)",
    state: "MA",
    year,
    ownership: "MTC",
    baseRoe,
    adjustmentBps: null,
    actualRoe: null,
    equityRatio,
    rateBase: null,
    revenueRequirement: null,
    revenueChange,
    docket,
    sourceIds,
    actualSourceIds: null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: "S22",
  };
}

function conedRow(year) {
  let baseRoe;
  let docket;
  let sourceIds;
  let sourceStatus;
  let annualizationNote;

  if (year === 2013) {
    baseRoe = 0.1015;
    docket = "09-E-0428";
    sourceIds = "S28";
    sourceStatus = "Reported carried-in rate";
    annualizationNote = "The 2014 order identifies 10.15% as the previously allowed electric ROE; it remained the year-end rate before the new plan began in 2014.";
  } else if (year <= 2015) {
    baseRoe = 0.0920;
    docket = "13-E-0030";
    sourceIds = "S28";
    sourceStatus = year === 2014 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2014
      ? "The two-year electric rate plan began 2014-01-01 with a 9.20% ROE."
      : "9.20% remained in force for the second year of the electric rate plan.";
  } else if (year === 2016) {
    baseRoe = 0.0900;
    docket = "15-E-0050 / 13-E-0030";
    sourceIds = "S29";
    sourceStatus = "Reported rate-plan extension";
    annualizationNote = "The extension order set a 9.00% ROE for calendar-year 2016.";
  } else if (year <= 2019) {
    baseRoe = 0.0900;
    docket = "16-E-0060";
    sourceIds = "S30";
    sourceStatus = year === 2017 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2017
      ? "The three-year electric rate plan began 2017-01-01 with a 9.00% ROE."
      : "9.00% carried forward under the 2017-2019 electric rate plan.";
  } else if (year <= 2022) {
    baseRoe = 0.0880;
    docket = "19-E-0065";
    sourceIds = "S31";
    sourceStatus = year === 2020 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2020
      ? "The three-year electric rate plan began 2020-01-01 with an 8.80% ROE."
      : "8.80% carried forward under the 2020-2022 electric rate plan.";
  } else {
    baseRoe = 0.0925;
    docket = "22-E-0064";
    sourceIds = "S32";
    sourceStatus = year === 2023 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2023
      ? "The 2023-2025 electric rate plan uses a 9.25% ROE; tariffs implementing the order took effect in August 2023."
      : "9.25% carried forward under the 2023-2025 electric rate plan.";
  }

  return {
    utilityId: 4226,
    utilityName: "Consolidated Edison Co-NY Inc",
    displayName: "Con Edison (CECONY)",
    state: "NY",
    year,
    ownership: "DOM",
    baseRoe,
    adjustmentBps: null,
    actualRoe: null,
    equityRatio: null,
    rateBase: null,
    revenueRequirement: null,
    revenueChange: null,
    docket,
    sourceIds,
    actualSourceIds: null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: "S37",
  };
}

function nysegRow(year) {
  let baseRoe;
  let docket;
  let sourceIds;
  let sourceStatus;
  let annualizationNote;

  if (year <= 2015) {
    baseRoe = 0.1000;
    docket = "09-E-0715";
    sourceIds = "S33";
    sourceStatus = year === 2013 ? "Reported carried-in rate" : "Reported and carried forward";
    annualizationNote = year === 2013
      ? "The 2010 rate order set a 10.00% ROE; the rate plan ran through 2013 and its provisions remained in effect until rates were reset."
      : "10.00% carried forward after the 2010 rate plan until the 2016 rate decision.";
  } else if (year <= 2019) {
    baseRoe = 0.0900;
    docket = "15-E-0283";
    sourceIds = "S34";
    sourceStatus = year === 2016 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2016
      ? "The order set a 9.00% ROE and tariffs took effect 2016-07-01."
      : "9.00% carried forward from the 2016 rate plan until rates were reset in 2020.";
  } else if (year <= 2022) {
    baseRoe = 0.0880;
    docket = "19-E-0378";
    sourceIds = "S35";
    sourceStatus = year === 2020 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2020
      ? "The rate plan uses an 8.80% ROE; tariffs implementing the order took effect 2020-12-01."
      : "8.80% carried forward under the 2020-2022 rate plan.";
  } else {
    baseRoe = 0.0920;
    docket = "22-E-0317";
    sourceIds = "S36";
    sourceStatus = year === 2023 ? "Reported final decision" : "Reported and carried forward";
    annualizationNote = year === 2023
      ? "The rate plan uses a 9.20% ROE; tariffs implementing the order took effect 2023-11-01."
      : "9.20% carried forward under the 2023-2026 rate plan.";
  }

  return {
    utilityId: 13511,
    utilityName: "New York State Elec & Gas Corp",
    displayName: "NYSEG",
    state: "NY",
    year,
    ownership: "MTC",
    baseRoe,
    adjustmentBps: null,
    actualRoe: null,
    equityRatio: null,
    rateBase: null,
    revenueRequirement: null,
    revenueChange: null,
    docket,
    sourceIds,
    actualSourceIds: null,
    annualizationNote,
    sourceStatus,
    ownershipSourceIds: "S13",
  };
}

const annual = [];
for (let year = 2013; year <= 2024; year += 1) annual.push(clpRow(year));
for (let year = 2013; year <= 2024; year += 1) annual.push(uiRow(year));
for (let year = 2013; year <= 2024; year += 1) annual.push(nstarRow(year));
for (let year = 2013; year <= 2024; year += 1) annual.push(mecoRow(year));
for (let year = 2013; year <= 2024; year += 1) annual.push(conedRow(year));
for (let year = 2013; year <= 2024; year += 1) annual.push(nysegRow(year));

const events = [
  ["E01", 4176, "Eversource Connecticut (CL&P)", null, "In force entering 2013", "Carried-in rate", "09-12-05", 0.0940, null, 0.0940, null, null, null, null, "Yes", "S01", "Beginning value for the pilot; earlier decision details are not reconstructed here."],
  ["E02", 19497, "United Illuminating", "2013-08", "August 2013", "Rate decision", "13-01-19", 0.0915, null, 0.0915, 0.50, null, null, null, "Yes", "S07; S15", "Raised ROE from 8.75% to 9.15%."],
  ["E03", 4176, "Eversource Connecticut (CL&P)", "2014-12-17", "2014-12-01", "Rate decision", "14-05-06", 0.0917, -15, 0.0902, null, null, null, 134.0, "Yes, for 2015 penalty year", "S02; S03; S16", "Base ROE was 9.17%; the 15 bp reduction was temporary and applied for one year."],
  ["E04", 19497, "United Illuminating", "2016-12-14", "2017-01-01", "Rate decision", "16-06-04", 0.0910, null, 0.0910, 0.50, 981.000, 363.034, 43.0, "Yes", "S17; S08", "Decision set three annual rate years; the stable SEC filing corroborates ROE and equity ratio, while the PURA database is the audit route for decision tables."],
  ["E05", 4176, "Eversource Connecticut (CL&P)", "2018-04-18", "2018-05-01", "Rate settlement", "17-10-46", 0.0925, null, 0.0925, 0.53, null, null, 64.3, "Yes", "S04", "Approved rate steps were $64.3m, $31.1m, and $29.2m for 2018-2020."],
  ["E06", 4176, "Eversource Connecticut (CL&P)", "2021-04-27", "Future rate proceeding", "Future penalty order", "20-08-03", 0.0925, -90, null, 0.53, null, null, null, "No", "S06", "The order required a future rate adjustment; 90 bp is not subtracted from 2021-2024 annual observations in this pilot."],
  ["E07", 19497, "United Illuminating", "2021-04-27", "Future rate proceeding", "Future penalty order", "20-08-03", 0.0910, -15, null, 0.50, null, null, null, "No", "S06", "The 15 bp order is stored as an event, not as an immediate change to the annual series."],
  ["E08", 19497, "United Illuminating", "2023-08-25", "2023-09-01", "Rate decision", "22-08-08", 0.0910, -47, 0.0863, 0.50, 1105.196, 384.865, 22.957, "Yes", "S10; S11", "Final decision controls: proposed-final materials cited different values. The final order uses 9.10%, 47 bp, and 8.63%."],
  ["E09", 54913, "NSTAR Electric (Eversource Massachusetts)", null, "In force entering 2013", "Carried-in rate", "D.T.E. 05-85", 0.1050, null, 0.1050, null, null, null, null, "Yes", "S18", "D.P.U. 17-05 identifies 10.50% as the then-current allowed ROE."],
  ["E10", 54913, "NSTAR Electric (Eversource Massachusetts)", "2017-11-30", "2018-02-01", "Rate decision", "D.P.U. 17-05", 0.1000, null, 0.1000, 0.5334, 2732.851801, null, null, "Yes", "S18; S27", "Official final order supports the ROE, capital structure, and decision-year rate base; the SEC filing verifies the compliance-rate effective date."],
  ["E11", 54913, "NSTAR Electric (Eversource Massachusetts)", "2022-11-30", "2023-01-01", "Rate decision", "D.P.U. 22-22", 0.0980, null, 0.0980, 0.532, null, null, 64.0, "Yes", "S19; S20", "SEC-filed annual report supplies the capital parameters; the DPU annual report cross-checks the decision and effective dates."],
  ["E12", 11804, "Massachusetts Electric (National Grid)", null, "In force entering 2013", "Carried-in rate", "D.P.U. 09-39", 0.1035, null, 0.1035, 0.50, null, null, null, "Yes", "S21; S22", "Official company annual report gives the allowed return and capital structure; D.P.U. 15-155 identifies the prior case."],
  ["E13", 11804, "Massachusetts Electric (National Grid)", "2016-09-30", "2016-10-01", "Rate decision", "D.P.U. 15-155", 0.0990, null, 0.0990, 0.51, null, null, 101.0, "Yes", "S23; S22", "National Grid's SEC-filed results report the approved ROE, equity ratio, and annual revenue increase."],
  ["E14", 11804, "Massachusetts Electric (National Grid)", "2019-09-30", "2019-10-01", "Rate decision", "D.P.U. 18-150", 0.0960, null, 0.0960, 0.535, null, null, 42.0, "Yes", "S24", "SEC-filed results report the approved capital parameters and initial annual revenue increase."],
  ["E15", 11804, "Massachusetts Electric (National Grid)", "2024-09-30", "November 2024 bills", "Rate decision", "D.P.U. 23-150", 0.0935, null, 0.0935, 0.5283, null, null, null, "Yes", "S25; S26", "Official DPU sources support the final capital parameters and customer-bill timing."],
  ["E16", 4226, "Con Edison (CECONY)", null, "In force entering 2013", "Carried-in rate", "09-E-0428", 0.1015, null, 0.1015, null, null, null, null, "Yes", "S28", "The 2014 order identifies 10.15% as the prior allowed electric ROE."],
  ["E17", 4226, "Con Edison (CECONY)", "2014-02-21", "2014-01-01", "Rate decision", "13-E-0030", 0.0920, null, 0.0920, null, null, null, null, "Yes", "S28", "The two-year electric rate plan used a 9.20% ROE for 2014-2015."],
  ["E18", 4226, "Con Edison (CECONY)", "2015-06-17", "2016-01-01", "Rate-plan extension", "15-E-0050 / 13-E-0030", 0.0900, null, 0.0900, null, null, null, null, "Yes", "S29", "The extension order set a 9.00% ROE for calendar-year 2016."],
  ["E19", 4226, "Con Edison (CECONY)", "2017-01-25", "2017-01-01", "Rate decision", "16-E-0060", 0.0900, null, 0.0900, null, null, null, null, "Yes", "S30", "The three-year electric rate plan used a 9.00% ROE for 2017-2019."],
  ["E20", 4226, "Con Edison (CECONY)", "2020-01-16", "2020-01-01", "Rate decision", "19-E-0065", 0.0880, null, 0.0880, null, null, null, null, "Yes", "S31", "The three-year electric rate plan used an 8.80% ROE for 2020-2022."],
  ["E21", 4226, "Con Edison (CECONY)", "2023-07-20", "2023 year-end", "Rate decision", "22-E-0064", 0.0925, null, 0.0925, null, null, null, null, "Yes", "S32", "The 2023-2025 electric rate plan uses a 9.25% ROE."],
  ["E22", 13511, "NYSEG", "2010-09-21", "In force entering 2013", "Carried-in rate", "09-E-0715", 0.1000, null, 0.1000, null, null, null, null, "Yes", "S33", "The 2010 rate order set a 10.00% ROE; its provisions remained until rates were reset."],
  ["E23", 13511, "NYSEG", "2016-06-15", "2016-07-01", "Rate decision", "15-E-0283", 0.0900, null, 0.0900, null, null, null, null, "Yes", "S34", "The rate plan used a 9.00% ROE; tariffs took effect July 2016."],
  ["E24", 13511, "NYSEG", "2020-11-19", "2020-12-01", "Rate decision", "19-E-0378", 0.0880, null, 0.0880, null, null, null, null, "Yes", "S35", "The 2020-2022 rate plan used an 8.80% ROE."],
  ["E25", 13511, "NYSEG", "2023-10-12", "2023-11-01", "Rate decision", "22-E-0317", 0.0920, null, 0.0920, null, null, null, null, "Yes", "S36", "The 2023-2026 rate plan uses a 9.20% ROE."],
];

const annualHeaders = [
  "utility_id_eia", "utility_name", "display_name", "state", "year", "ownership",
  "base_authorized_roe", "performance_adjustment_bps", "effective_authorized_roe",
  "actual_earned_roe", "actual_minus_effective_bps", "approved_equity_ratio",
  "approved_rate_base_million_usd", "authorized_equity_return_million_usd",
  "approved_distribution_revenue_requirement_million_usd", "equity_return_share_of_revenue_requirement",
  "approved_incremental_revenue_change_million_usd", "docket", "source_ids", "actual_roe_source_ids",
  "source_status", "annualization_note", "ownership_source_ids",
];

function effectiveRoe(row) {
  return row.baseRoe == null ? null : row.baseRoe + (row.adjustmentBps ?? 0) / 10000;
}

function derivedAnnualRows() {
  const round = (value, digits) => value == null ? null : Number(value.toFixed(digits));
  return annual.map((row) => {
    const effective = effectiveRoe(row);
    const actualGap = row.actualRoe == null || effective == null ? null : (row.actualRoe - effective) * 10000;
    const equityReturn = row.rateBase == null || row.equityRatio == null || effective == null
      ? null
      : row.rateBase * row.equityRatio * effective;
    const equityShare = equityReturn == null || row.revenueRequirement == null
      ? null
      : equityReturn / row.revenueRequirement;
    return [
      row.utilityId, row.utilityName, row.displayName, row.state, row.year, row.ownership,
      row.baseRoe, row.adjustmentBps, round(effective, 6), row.actualRoe, round(actualGap, 2), row.equityRatio,
      row.rateBase, round(equityReturn, 6), row.revenueRequirement, round(equityShare, 8), row.revenueChange,
      row.docket, row.sourceIds, row.actualSourceIds, row.sourceStatus, row.annualizationNote,
      row.ownershipSourceIds,
    ];
  });
}

function csvEscape(value) {
  if (value == null) return "";
  const text = String(value);
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function toCsv(headers, rows) {
  return [headers, ...rows].map((row) => row.map(csvEscape).join(",")).join("\n") + "\n";
}

function styleTitle(sheet, rangeAddress, title) {
  const range = sheet.getRange(rangeAddress);
  range.merge();
  range.values = [[title]];
  range.format.fill = "#17324D";
  range.format.font = { bold: true, color: "#FFFFFF", size: 18 };
  range.format.verticalAlignment = "center";
  range.format.rowHeight = 34;
}

function styleSubtitle(sheet, rangeAddress, subtitle) {
  const range = sheet.getRange(rangeAddress);
  range.merge();
  range.values = [[subtitle]];
  range.format.fill = "#EAF1F6";
  range.format.font = { color: "#334E68", italic: true, size: 10 };
  range.format.wrapText = true;
  range.format.rowHeight = 32;
}

function styleHeader(range) {
  range.format.fill = "#2E5D73";
  range.format.font = { bold: true, color: "#FFFFFF", size: 9 };
  range.format.wrapText = true;
  range.format.verticalAlignment = "center";
  range.format.rowHeight = 34;
  range.format.borders = { preset: "outside", style: "thin", color: "#A8BAC5" };
}

function setColumnWidths(sheet, widths) {
  widths.forEach(([address, width]) => {
    sheet.getRange(address).format.columnWidth = width;
  });
}

async function buildWorkbook() {
  const workbook = Workbook.create();
  const readme = workbook.worksheets.add("Read me");
  const annualSheet = workbook.worksheets.add("Annual pilot");
  const eventSheet = workbook.worksheets.add("Rate case events");
  const ownershipSheet = workbook.worksheets.add("Ownership sources");
  const sourceSheet = workbook.worksheets.add("Source register");

  for (const sheet of [readme, annualSheet, eventSheet, ownershipSheet, sourceSheet]) {
    sheet.showGridLines = false;
  }

  styleTitle(readme, "A1:F1", "Matched-state authorized-ROE pilot, 2013-2024");
  styleSubtitle(readme, "A2:F2", "Three domestic/multinational utility pairs under the same state regulator in Connecticut, Massachusetts, and New York. This is a source audit and descriptive check, not a causal test.");
  readme.getRange("A4:B4").values = [["Pilot scope", "What is settled"]];
  styleHeader(readme.getRange("A4:B4"));
  readme.getRange("A5:B9").values = [
    ["Utilities", "Connecticut: CL&P and UI. Massachusetts: NSTAR and Massachusetts Electric. New York: Con Edison and NYSEG. Each state has one 2024 DOM utility and one MTC utility."],
    ["Years", "2013-2024; authorized values are year-end snapshots, while EIA prices used on the website are full-year averages"],
    ["Regulators", "Connecticut PURA, Massachusetts DPU, and New York PSC"],
    ["Source rule", "Official regulator, state advocate, SEC, and utility filings; blanks remain blank when a defensible figure was not found"],
    ["Current use", "Use full-year price and year-end authorized ROE as a descriptive direction check within each state; do not treat them as perfectly time-aligned or causal"],
  ];
  readme.getRange("A11:B11").values = [["Term", "Plain-language meaning"]];
  styleHeader(readme.getRange("A11:B11"));
  readme.getRange("A12:B18").values = [
    ["Base authorized ROE", "The regulator-approved return percentage on the shareholder-funded part of rate base before a separately stated performance penalty."],
    ["Effective authorized ROE (year-end)", "Base authorized ROE after an adjustment that is actually in force at calendar year-end. A future-proceeding order is not treated as immediately effective."],
    ["Actual earned ROE", "What the utility reported earning. In this pilot it is available only for UI in 2017-2021 from an OCC filing."],
    ["Rate base", "The regulator-approved value of utility assets used to provide regulated service, net of specified adjustments."],
    ["Authorized common-equity return component", "A transparent derived component: approved rate base × approved equity ratio × effective authorized ROE. It is not shareholder compensation, dividends, a customer price, or total profit."],
    ["Revenue requirement", "The annual regulated distribution revenue the decision allows the utility to collect, where the source reports it."],
    ["Blank cell", "Not found, not reported for that rate year, or not applicable. Blank never means zero."],
  ];
  readme.getRange("A20:B20").values = [["What this first step shows", "What it does not show"]];
  styleHeader(readme.getRange("A20:B20"));
  readme.getRange("A21:B23").values = [
    ["The annual series keeps base ROE, penalties, and actual earned ROE separate.", "It does not establish that ROE caused a price difference."],
    ["In 2024 the MTC utility had the lower ROE in all three states, but its price was higher in Connecticut and Massachusetts and lower in New York.", "Authorized ROE is one distribution-cost input; it is not a complete customer-bill explanation."],
    ["The 2021 Isaias penalties remain future-order events and are not silently subtracted from 2021 observations.", "Six utilities are still not representative of all MTC or DOM utilities."],
  ];
  readme.getRange("A25:F25").merge();
  readme.getRange("A25:F25").values = [["Next: present the three matched-state comparisons as a sourced preliminary finding before deciding whether ROE belongs in a wider panel model."]];
  readme.getRange("A25:F25").format = {
    fill: "#FFF4D6",
    font: { bold: true, color: "#5B4600" },
    wrapText: true,
    rowHeight: 42,
    borders: { preset: "outside", style: "thin", color: "#D6B85B" },
  };
  readme.getRange("A5:B23").format.wrapText = true;
  readme.getRange("A5:B23").format.verticalAlignment = "top";
  readme.getRange("A5:B23").format.borders = { preset: "inside", style: "thin", color: "#DDE6EC" };
  setColumnWidths(readme, [["A:A", 28], ["B:B", 92], ["C:F", 12]]);
  readme.freezePanes.freezeRows(2);

  styleTitle(annualSheet, "A1:W1", "Annual authorized-ROE pilot");
  styleSubtitle(annualSheet, "A2:W2", "Values are year-end rates in force. Decision-year dollar inputs stay attached to the rate year reported; they are not automatically carried forward. Derived columns are formulas.");
  annualSheet.getRange("A4:W4").values = [annualHeaders];
  styleHeader(annualSheet.getRange("A4:W4"));
  const annualValues = annual.map((row) => [
    row.utilityId, row.utilityName, row.displayName, row.state, row.year, row.ownership,
    row.baseRoe, row.adjustmentBps, null, row.actualRoe, null, row.equityRatio,
    row.rateBase, null, row.revenueRequirement, null, row.revenueChange, row.docket,
    row.sourceIds, row.actualSourceIds, row.sourceStatus, row.annualizationNote, row.ownershipSourceIds,
  ]);
  annualSheet.getRange(`A5:W${4 + annualValues.length}`).values = annualValues;
  annualSheet.getRange("I5").formulas = [["=IF(G5=\"\",\"\",G5+IF(H5=\"\",0,H5)/10000)"]];
  annualSheet.getRange(`I5:I${4 + annualValues.length}`).fillDown();
  annualSheet.getRange("K5").formulas = [["=IF(J5=\"\",\"\",(J5-I5)*10000)"]];
  annualSheet.getRange(`K5:K${4 + annualValues.length}`).fillDown();
  annualSheet.getRange("N5").formulas = [["=IF(M5=\"\",\"\",M5*L5*I5)"]];
  annualSheet.getRange(`N5:N${4 + annualValues.length}`).fillDown();
  annualSheet.getRange("P5").formulas = [["=IF(O5=\"\",\"\",N5/O5)"]];
  annualSheet.getRange(`P5:P${4 + annualValues.length}`).fillDown();
  annualSheet.getRange(`G5:G${4 + annualValues.length}`).setNumberFormat("0.00%");
  annualSheet.getRange(`I5:J${4 + annualValues.length}`).setNumberFormat("0.00%");
  annualSheet.getRange(`L5:L${4 + annualValues.length}`).setNumberFormat("0%");
  annualSheet.getRange(`P5:P${4 + annualValues.length}`).setNumberFormat("0.0%");
  annualSheet.getRange(`H5:H${4 + annualValues.length}`).setNumberFormat("0");
  annualSheet.getRange(`K5:K${4 + annualValues.length}`).setNumberFormat("0");
  annualSheet.getRange(`M5:O${4 + annualValues.length}`).setNumberFormat("$#,##0.000");
  annualSheet.getRange(`Q5:Q${4 + annualValues.length}`).setNumberFormat("$#,##0.000");
  annualSheet.getRange(`A5:W${4 + annualValues.length}`).format.verticalAlignment = "top";
  annualSheet.getRange(`B5:C${4 + annualValues.length}`).format.wrapText = true;
  annualSheet.getRange(`S5:W${4 + annualValues.length}`).format.wrapText = true;
  annualSheet.getRange(`N5:N${4 + annualValues.length}`).format.fill = "#EAF4EA";
  annualSheet.getRange(`K5:K${4 + annualValues.length}`).format.fill = "#F2F4F5";
  const annualTable = annualSheet.tables.add(`A4:W${4 + annualValues.length}`, true, "AnnualRoePilotTable");
  annualTable.style = "TableStyleMedium2";
  annualTable.showBandedColumns = false;
  annualSheet.freezePanes.freezeRows(4);
  annualSheet.freezePanes.freezeColumns(3);
  setColumnWidths(annualSheet, [
    ["A:A", 12], ["B:C", 28], ["D:D", 7], ["E:F", 10], ["G:J", 15], ["K:K", 14],
    ["L:L", 14], ["M:Q", 18], ["R:R", 24], ["S:U", 17], ["V:V", 58], ["W:W", 18],
  ]);

  const eventHeaders = [
    "event_id", "utility_id_eia", "display_name", "decision_date", "effective_date",
    "event_type", "docket", "base_authorized_roe", "ordered_adjustment_bps",
    "effective_authorized_roe_in_force", "approved_equity_ratio", "approved_rate_base_million_usd",
    "approved_distribution_revenue_requirement_million_usd", "approved_incremental_revenue_change_million_usd",
    "applied_to_annual_series", "source_ids", "notes",
  ];
  styleTitle(eventSheet, "A1:Q1", "Rate-case and penalty event register");
  styleSubtitle(eventSheet, "A2:Q2", "This sheet separates an order from the year when it actually changes the annual series. Future-proceeding penalties remain visible without being treated as immediately effective.");
  eventSheet.getRange("A4:Q4").values = [eventHeaders];
  styleHeader(eventSheet.getRange("A4:Q4"));
  eventSheet.getRange(`A5:Q${4 + events.length}`).values = events;
  eventSheet.getRange(`H5:H${4 + events.length}`).setNumberFormat("0.00%");
  eventSheet.getRange(`J5:K${4 + events.length}`).setNumberFormat("0.00%");
  eventSheet.getRange(`L5:N${4 + events.length}`).setNumberFormat("$#,##0.000");
  eventSheet.getRange(`C5:Q${4 + events.length}`).format.wrapText = true;
  eventSheet.getRange(`A5:Q${4 + events.length}`).format.verticalAlignment = "top";
  const eventTable = eventSheet.tables.add(`A4:Q${4 + events.length}`, true, "RateCaseEventsTable");
  eventTable.style = "TableStyleMedium2";
  eventSheet.freezePanes.freezeRows(4);
  setColumnWidths(eventSheet, [
    ["A:B", 11], ["C:C", 28], ["D:E", 15], ["F:G", 17], ["H:J", 16], ["K:K", 14],
    ["L:N", 19], ["O:P", 18], ["Q:Q", 66],
  ]);

  const ownershipHeaders = ["utility_id_eia", "utility_name", "start_year", "end_year", "ownership", "ultimate_parent_or_owner", "parent_country_or_level", "source_ids", "coding_note"];
  styleTitle(ownershipSheet, "A1:I1", "Ownership coding used in the pilot");
  styleSubtitle(ownershipSheet, "A2:I2", "The ownership variable follows the project's four-category rule. Pair matching uses 2024 ownership; UI's earlier DOM years remain visible in the annual data.");
  ownershipSheet.getRange("A4:I4").values = [ownershipHeaders];
  styleHeader(ownershipSheet.getRange("A4:I4"));
  ownershipSheet.getRange(`A5:I${4 + ownershipRows.length}`).values = ownershipRows;
  ownershipSheet.getRange(`A5:I${4 + ownershipRows.length}`).format.wrapText = true;
  ownershipSheet.getRange(`A5:I${4 + ownershipRows.length}`).format.verticalAlignment = "top";
  const ownershipTable = ownershipSheet.tables.add(`A4:I${4 + ownershipRows.length}`, true, "OwnershipSourcesTable");
  ownershipTable.style = "TableStyleMedium2";
  ownershipSheet.freezePanes.freezeRows(4);
  setColumnWidths(ownershipSheet, [["A:A", 14], ["B:B", 30], ["C:E", 11], ["F:G", 28], ["H:H", 16], ["I:I", 62]]);

  const sourceHeaders = ["source_id", "issuer", "source_title", "source_date_or_retrieved_date", "source_url", "source_location", "variables_supported", "quality_and_use_note"];
  styleTitle(sourceSheet, "A1:H1", "Source register");
  styleSubtitle(sourceSheet, "A2:H2", "Every annual or event row points here by source ID. URLs lead to official government, SEC, or company sources; source notes identify any database lookup needed for an older decision.");
  sourceSheet.getRange("A4:H4").values = [sourceHeaders];
  styleHeader(sourceSheet.getRange("A4:H4"));
  sourceSheet.getRange(`A5:H${4 + sources.length}`).values = sources;
  sourceSheet.getRange(`A5:H${4 + sources.length}`).format.wrapText = true;
  sourceSheet.getRange(`A5:H${4 + sources.length}`).format.verticalAlignment = "top";
  const sourceTable = sourceSheet.tables.add(`A4:H${4 + sources.length}`, true, "RoeSourceRegisterTable");
  sourceTable.style = "TableStyleMedium2";
  sourceSheet.freezePanes.freezeRows(4);
  setColumnWidths(sourceSheet, [["A:A", 10], ["B:B", 32], ["C:C", 42], ["D:D", 18], ["E:E", 58], ["F:F", 24], ["G:G", 52], ["H:H", 48]]);

  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  await fs.mkdir(PROCESSED_DIR, { recursive: true });

  const xlsx = await SpreadsheetFile.exportXlsx(workbook);
  const outputPath = path.join(OUTPUT_DIR, "roe_pilot_2013_2024.xlsx");
  await xlsx.save(outputPath);

  const annualCsvRows = derivedAnnualRows();
  await fs.writeFile(
    path.join(PROCESSED_DIR, "roe_annual_pilot_2013_2024.csv"),
    toCsv(annualHeaders, annualCsvRows),
    "utf8",
  );
  await fs.writeFile(
    path.join(PROCESSED_DIR, "roe_rate_case_events.csv"),
    toCsv(eventHeaders, events),
    "utf8",
  );
  await fs.writeFile(
    path.join(PROCESSED_DIR, "roe_ownership_sources.csv"),
    toCsv(ownershipHeaders, ownershipRows),
    "utf8",
  );
  await fs.writeFile(
    path.join(PROCESSED_DIR, "roe_source_register.csv"),
    toCsv(sourceHeaders, sources),
    "utf8",
  );

  const sheetNames = ["Read me", "Annual pilot", "Rate case events", "Ownership sources", "Source register"];
  for (const sheetName of sheetNames) {
    const preview = await workbook.render({ sheetName, autoCrop: "all", scale: 0.9, format: "png" });
    const bytes = new Uint8Array(await preview.arrayBuffer());
    await fs.writeFile(path.join(PREVIEW_DIR, `${sheetName.toLowerCase().replaceAll(" ", "-")}.png`), bytes);
  }

  const inspection = await workbook.inspect({
    kind: "workbook,sheet,table",
    maxChars: 8000,
    tableMaxRows: 5,
    tableMaxCols: 8,
    tableMaxCellChars: 90,
  });
  const annualInspection = await workbook.inspect({
    kind: "region",
    sheetId: "Annual pilot",
    range: "A1:W12",
    maxChars: 8000,
  });
  const formulaInspection = await workbook.inspect({
    kind: "formula",
    sheetId: "Annual pilot",
    range: `I5:P${4 + annual.length}`,
    maxChars: 8000,
    options: { maxResults: 100 },
  });

  const formulaErrors = [];
  for (const sheetName of sheetNames) {
    const values = workbook.worksheets.getItem(sheetName).getUsedRange()?.values ?? [];
    values.forEach((row, rowIndex) => row.forEach((value, colIndex) => {
      if (typeof value === "string" && /^#(REF!|DIV\/0!|VALUE!|NAME\?|N\/A|NUM!|NULL!)/.test(value)) {
        formulaErrors.push({ sheetName, row: rowIndex + 1, col: colIndex + 1, value });
      }
    }));
  }

  console.log(JSON.stringify({
    outputPath,
    annualRows: annual.length,
    eventRows: events.length,
    sourceRows: sources.length,
    formulaErrors,
    inspection: inspection.ndjson,
    annualInspection: annualInspection.ndjson,
    formulaInspection: formulaInspection.ndjson,
  }, null, 2));
}

await buildWorkbook();
