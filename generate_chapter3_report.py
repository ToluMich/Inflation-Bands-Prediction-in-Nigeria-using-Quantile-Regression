from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Inches, Pt, RGBColor


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "Chapter_3_Methodology_Referenced.docx"


def add_text(doc, text, style=None):
    paragraph = doc.add_paragraph(style=style)
    paragraph.add_run(text)
    return paragraph


def add_bullets(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Bullet")


def add_numbered(doc, items):
    for item in items:
        doc.add_paragraph(item, style="List Number")


def add_heading(doc, text, level=1):
    return doc.add_heading(text, level=level)


def set_cell_text(cell, text, bold=False, color=None):
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(str(text))
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_caption(doc, text):
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run(text)
    run.italic = True
    run.font.size = Pt(9)
    return paragraph


def make_code_image(source_lines, output_path, title):
    font_paths = [
        r"C:\Windows\Fonts\consolas.ttf",
        r"C:\Windows\Fonts\cour.ttf",
    ]
    font_path = next((path for path in font_paths if Path(path).exists()), None)
    font = ImageFont.truetype(font_path, 18) if font_path else ImageFont.load_default()
    title_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    wrapped = source_lines
    line_height = 28
    width = 1650
    height = 110 + len(wrapped) * line_height
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, width, 66), fill="#17365D")
    draw.text((35, 18), title, fill="white", font=title_font)
    y = 82
    for index, line in enumerate(wrapped, start=1):
        number = f"{index:02d}"
        draw.text((25, y), number, fill="#777777", font=font)
        draw.text((80, y), line.expandtabs(4).rstrip(), fill="#202020", font=font)
        y += line_height
    image.save(output_path, quality=95)


def configure_document(doc):
    section = doc.sections[0]
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.0)
    section.right_margin = Cm(2.54)

    styles = doc.styles
    styles["Normal"].font.name = "Times New Roman"
    styles["Normal"].font.size = Pt(12)
    styles["Normal"].paragraph_format.line_spacing = 1.5
    styles["Normal"].paragraph_format.space_after = Pt(6)

    for style_name in ["Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"]:
        styles[style_name].font.name = "Times New Roman"
    styles["Heading 1"].font.size = Pt(16)
    styles["Heading 1"].font.color.rgb = RGBColor(23, 54, 93)
    styles["Heading 2"].font.size = Pt(14)
    styles["Heading 2"].font.color.rgb = RGBColor(23, 54, 93)
    styles["Heading 3"].font.size = Pt(12)
    styles["Heading 3"].font.color.rgb = RGBColor(23, 54, 93)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    header = table.rows[0].cells
    for index, heading in enumerate(headers):
        set_cell_text(header[index], heading, bold=True, color=(255, 255, 255))
        header[index]._tc.get_or_add_tcPr().append(
            __import__("docx").oxml.parse_xml(
                r'<w:shd {} w:fill="17365D"/>'.format(
                    'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
                )
            )
        )
    for row in rows:
        cells = table.add_row().cells
        for index, value in enumerate(row):
            set_cell_text(cells[index], value)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Cm(width)
    return table


main_source = (BASE_DIR / "main.py").read_text(encoding="utf-8").splitlines()

data_code = main_source[14:39]
model_code = main_source[40:61]
evaluation_code = main_source[62:91]
plot_code = main_source[113:159]

snippet_paths = []
for title, lines, filename in [
    ("Data alignment and next-month target", data_code, "data_alignment_code.png"),
    ("Quantile-regression model fitting", model_code, "quantile_models_code.png"),
    ("Coverage evaluation", evaluation_code, "coverage_code.png"),
    ("Colour-coded graph construction", plot_code, "graph_code.png"),
]:
    path = BASE_DIR / filename
    make_code_image(lines, path, title)
    snippet_paths.append(path)

doc = Document()
configure_document(doc)

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = title.add_run("CHAPTER THREE")
run.bold = True
run.font.size = Pt(18)
run.font.name = "Times New Roman"

subtitle = doc.add_paragraph()
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = subtitle.add_run("RESEARCH METHODOLOGY")
run.bold = True
run.font.size = Pt(16)

add_heading(doc, "3.1 Introduction", 1)
add_text(
    doc,
    "This chapter presents the research design and procedures used to develop and evaluate "
    "a next-month inflation forecasting model for Nigeria. The study adopts a quantitative, "
    "time-series research design based on quantile regression. Quantile regression is appropriate "
    "because point forecasts do not adequately communicate uncertainty. The project therefore "
    "models the conditional 0.10, 0.50 and 0.90 quantiles of next-month inflation and uses the "
    "interval between the first and third quantiles as an estimated 80 percent prediction band. "
    "The methodology covers data compilation, variable definition, chronological data splitting, "
    "model estimation, forecasting, band evaluation and graphical presentation."
)
add_text(
    doc,
    "The completed implementation is contained in the main Python programme included with the "
    "project. Its central principle is that each forecast must be made only from information "
    "available at the relevant forecast origin. For example, observations recorded for month t "
    "are used to predict inflation in month t + 1. This structure avoids the use of future values "
    "as predictors and is consistent with the assignment's next-month forecasting objective."
)

add_heading(doc, "3.2 Research Design", 1)
add_text(
    doc,
    "The study is designed as an out-of-sample forecasting exercise. A chronological split is "
    "used because randomly separating observations would allow information from nearby months to "
    "appear in both the training and test samples and would compromise the temporal interpretation "
    "of the results. The specification was implemented with:"
)
add_bullets(
    doc,
    [
        "training observations for dates before 1 January 2023;",
        "out-of-sample test observations from 1 January 2023 to 30 November 2025; and",
        "next-month inflation targets calculated from the inflation observation immediately following each forecast-origin month.",
    ],
)
add_text(
    doc,
    "The end point is November 2025 because December inflation would be the forecast target for "
    "the November origin. December 2025 is therefore not used as a forecast origin in the reported "
    "test set, since its next-month target is outside the available December 2025 dataset. This "
    "accounts for the 35 forecast months produced by the programme rather than 36 consecutive "
    "calendar months."
)

add_heading(doc, "3.3 Study Scope and Source Variables", 1)
add_text(
    doc,
    "The complete monthly working dataset contains 192 observations covering January 2010 to "
    "December 2025. Its intended variables are the National Bureau of Statistics headline inflation "
    "rate, the Central Bank of Nigeria Monetary Policy Rate, the Nigerian naira exchange rate per "
    "United States dollar, and the NBS food price index. The study's original variable description "
    "also referred to oil price, but oil was not retained as a predictor in the final implementation "
    "because the specification supplied for the final model explicitly required inflation lag, MPR, "
    "exchange rate and food index."
)
add_table(
    doc,
    ["Variable", "Description", "Role in the model"],
    [
        ["Date", "Month-end observation date", "Temporal identifier and forecast origin"],
        ["Inflation", "Headline inflation rate (%)", "Forecast target after one-month shift"],
        ["Inflation_Lag1", "Inflation available at forecast origin", "Autoregressive predictor"],
        ["MPR", "Central Bank Monetary Policy Rate (%)", "Policy predictor"],
        ["Exchange_Rate_NGN_USD", "Monthly naira/dollar exchange rate", "External-sector predictor"],
        ["Food_Index", "NBS food price index", "Domestic price predictor"],
    ],
    [3.2, 6.1, 5.3],
)

add_heading(doc, "3.4 Data Acquisition and Compilation", 1)
add_text(
    doc,
    "Data collection proceeded from the institutional sources associated with the project brief. "
    "The NBS e-library was treated as the principal source for Nigerian CPI, inflation and food "
    "index information, while the CBN provided MPR and exchange-rate information. Relevant files "
    "and source records are retained in the project directory for transparency. However, obtaining "
    "machine-readable, complete monthly official files covering the full requested period was not "
    "always possible through public web interfaces. Consequently, the single working dataset contains "
    "values with different provenance and several reconstructed or secondary observations."
)
add_text(
    doc,
    "This distinction is methodologically important. For academic reporting, reconstructed data "
    "cannot be presented as if they were direct official observations. Before the study is submitted "
    "as an empirical NBS/CBN analysis, missing official monthly observations must be replaced using "
    "archived NBS publications and verified CBN statistical tables or bulletins, with the precise "
    "source publication recorded for each observation. This report therefore describes the completed "
    "coding workflow while treating the numerical results as preliminary rather than independently "
    "confirmed official data."
)

add_heading(doc, "3.4.1 Monthly Alignment", 1)
add_text(
    doc,
    "Each series was converted to a month-end datetime or aggregated to monthly observations where "
    "the source contained higher-frequency records. The source tables were then merged on Date. "
    "This prevents an observation from one month being accidentally combined with a record from a "
    "different reporting period. Numeric columns were converted to decimal values and missing values "
    "were checked explicitly. Daily or frequent exchange-rate observations, if used, would require "
    "monthly aggregation; the monthly field used by the final programme is the value in the compiled "
    "dataset under Exchange_Rate_NGN_USD."
)

doc.add_picture(str(snippet_paths[0]), width=Inches(6.2))
add_caption(doc, "Figure 3.1: Screenshot of data alignment and target construction in the implementation.")

add_heading(doc, "3.5 Variable Engineering and Forecast-Target Alignment", 1)
add_text(
    doc,
    "The programme creates the target variable using the pandas shift operation:"
)
add_text(doc, "Inflation_Next_Month(t) = Inflation(t + 1).", style="Intense Quote")
add_text(
    doc,
    "For example, inflation in January 2010 would act as the predictor associated with February "
    "2010 inflation as the target. Likewise, an observation dated December 2025 has no following "
    "month in the dataset and is consequently removed after the target shift creates its missing "
    "value. This target convention should not be confused with predicting inflation at month t from "
    "future observations in month t + 1. The predictor variables are all taken from the current "
    "forecast-origin row, while the dependent variable is the immediately subsequent inflation "
    "observation."
)
add_text(
    doc,
    "The variable Inflation_Lag1 is named to reflect its position relative to the target, even "
    "though the source value at the forecast-origin row is current-month inflation. MPR, exchange "
    "rate and food index are attached to the same origin row. The implementation also computes a "
    "Forecast_Month as the month-end following the origin date. This field identifies the target "
    "period in the prediction output."
)

add_heading(doc, "3.6 Model Specification", 1)
add_text(
    doc,
    "Quantile regression estimates the relationship between predictors and different conditional "
    "quantiles of the target distribution. Unlike ordinary least squares, which estimates the "
    "conditional mean, quantile regression estimates the conditional median or other specified "
    "parts of the conditional distribution. As formalised by Koenker and Bassett (1978), the "
    "linear model for a selected quantile tau is:"
)
add_text(
    doc,
    "Q_y(tau | X) = beta_0(tau) + beta_1(tau)Inflation_Lag1 "
    "+ beta_2(tau)MPR + beta_3(tau)Exchange_Rate + beta_4(tau)Food_Index.",
    style="Intense Quote",
)
add_text(
    doc,
    "The parameters beta_0 through beta_4 were estimated separately for tau = 0.10, 0.50 and "
    "0.90. They are not obtained from a single fitted mean model and then added as constant "
    "bands. Each tau value has its own coefficient vector. Tau = 0.10 is interpreted as the lower "
    "conditional quantile, tau = 0.50 as the median, and tau = 0.90 as the upper conditional "
    "quantile (Koenker and Hallock, 2001)."
)
add_text(
    doc,
    "The model is estimated with statsmodels.formula.api.quantreg. The model formula is:"
)
add_text(
    doc,
    "Inflation_Next_Month ~ Inflation_Lag1 + MPR_Lag1 + FX_Rate_Lag1 + Food_Index_Lag1.",
    style="Intense Quote",
)
add_text(
    doc,
    "Each fitted quantile is represented by a separate object in the models dictionary. Test "
    "observations are passed only to the fitted models to obtain predicted quantiles; no test "
    "target is used in fitting."
)
doc.add_picture(str(snippet_paths[1]), width=Inches(6.2))
add_caption(doc, "Figure 3.2: Screenshot of the three quantile regressions implemented in Python.")

add_heading(doc, "3.7 Handling Quantile Crossing", 1)
add_text(
    doc,
    "Independent estimates of conditional quantiles may occasionally violate the theoretical "
    "ordering because sampling variation causes quantile curves to cross. Where the raw output "
    "orders all three estimates incorrectly, post-processing can reorder the three predictions "
    "within each forecast month. In the current implementation, the three predictions for one "
    "month are sorted and assigned to q10, q50 and q90. Sorting is applied only after fitting and "
    "does not alter the training process. It ensures that the lower quantile does not exceed the "
    "median and that the median does not exceed the upper quantile."
)
add_text(
    doc,
    "It should be noted that simple sorting is a numerical consistency adjustment, not a full "
    "joint constrained quantile model. A stricter implementation could use simultaneous constrained "
    "quantile estimation or bootstrap calibration. The sorting step is documented here because it "
    "affects the displayed interval and coverage calculation."
)

add_heading(doc, "3.8 Training and Forecasting Procedure", 1)
add_numbered(
    doc,
    [
        "The working dataset is read and sorted in ascending chronological order to preserve temporal structure.",
        "Column names are standardised so that exchange-rate values are addressed as FX_Rate by the model formula.",
        "The following-month inflation target and forecast-origin variables are created.",
        "Rows with missing modelling variables or the absent final next-month target are removed from estimation.",
        "Rows dated before January 2023 are assigned to the training set, while forecast origins from January 2023 through November 2025 are assigned to the test set.",
        "Quantile-regression models are estimated independently for tau = 0.10, 0.50 and 0.90 using the training set only.",
        "The three fitted models generate q10, q50 and q90 forecasts for every test observation.",
        "The forecasts are sorted within each month where necessary, producing a non-crossing prediction band.",
        "The programme records the test actual, median forecast, lower and upper quantiles, and band-membership indicator.",
    ],
)

add_heading(doc, "3.9 Evaluation of the 80 Percent Prediction Band", 1)
add_text(
    doc,
    "The 80 percent prediction band is defined by:"
)
add_text(doc, "B(t) = [Q_0.10(Y(t+1)|X(t)), Q_0.90(Y(t+1)|X(t))].", style="Intense Quote")
add_text(
    doc,
    "A forecast is considered covered when the actual next-month inflation rate is equal to or "
    "greater than the lower quantile and equal to or less than the upper quantile. Empirical coverage "
    "is calculated as the percentage of test observations that satisfy these conditions:"
)
add_text(doc, "Coverage = (number of observations inside the band / total test observations) x 100.", style="Intense Quote")
add_text(
    doc,
    "The evaluation therefore provides a simple empirical interpretation of interval calibration. "
    "A coverage close to 80 percent would indicate that the model's nominal 80 percent band contained "
    "approximately 80 percent of the realised inflation values in the out-of-sample period. Coverage "
    "substantially below 80 percent indicates under-coverage, while coverage substantially above 80 "
    "percent may indicate a band that is excessively wide."
)
doc.add_picture(str(snippet_paths[2]), width=Inches(6.2))
add_caption(doc, "Figure 3.3: Screenshot of empirical band coverage calculation.")

add_heading(doc, "3.10 Model Results Recorded in the Programme", 1)
add_text(
    doc,
    "For the compiled working dataset, the programme reported 35 forecast months, nine observations "
    "inside the fitted 80 percent band and empirical coverage of 25.71 percent. This result is "
    "reported in the final output table and should not be described as evidence that the officially "
    "sourced model achieved only 25.71 percent coverage until the complete data provenance has been "
    "validated. In particular, the 2024-2025 portion of the working dataset contains observations "
    "whose compilation required secondary and reconstructed values. The model's apparent failure "
    "may therefore reflect data inconsistency, a model specification problem, quantile crossing "
    "handling, structural breaks or a combination of these factors."
)
add_table(
    doc,
    ["Metric", "Value"],
    [
        ["Target coverage", "80.00 percent"],
        ["Test forecast months", "35"],
        ["Forecasts inside band", "9"],
        ["Empirical coverage", "25.71 percent"],
    ],
    [9.0, 5.0],
)
add_caption(doc, "Table 3.1: Coverage summary generated by the implementation.")

add_heading(doc, "3.11 Visualisation Procedure", 1)
add_text(
    doc,
    "The prediction outputs are plotted against their target forecast month. The programme uses "
    "five visual elements: a black actual-inflation line, a blue dashed median line, an orange "
    "lower quantile line, a green upper quantile line and a light pink translucent area representing "
    "the interval between the lower and upper quantiles. Grid lines aid interpretation, while distinct "
    "colours and line styles permit differentiation even for viewers with limited colour discrimination."
)
add_text(
    doc,
    "The plot is opened using matplotlib's interactive display function. The user can inspect the "
    "figure and save it through the graphical interface. The programme also exports predictions and "
    "coverage statistics to CSV files so that the graphical display is reproducible from numerical "
    "outputs."
)
doc.add_picture(str(snippet_paths[3]), width=Inches(6.2))
add_caption(doc, "Figure 3.4: Screenshot of the colour-coded plot configuration.")

if (BASE_DIR / "nigeria_inflation_quantile_bands.png").exists():
    doc.add_picture(str(BASE_DIR / "nigeria_inflation_quantile_bands.png"), width=Inches(6.35))
    add_caption(doc, "Figure 3.5: Generated forecast plot from the current working dataset.")

add_heading(doc, "3.12 Data and Model Validation", 1)
add_text(
    doc,
    "Several validation steps are required before the final empirical findings can be presented "
    "with institutional confidence. First, all source observations should be checked against official "
    "NBS releases and the exact reporting definitions should be confirmed. The working period includes "
    "base-year changes and index revisions that may affect comparability if the values were not "
    "adjusted consistently. Second, MPR observations should be matched to the date on which each "
    "MPC decision became effective, rather than assigned to a decision meeting date without checking "
    "the implementation period. Third, exchange rates require a clearly documented convention. One "
    "choice would be the monthly average rate; another would be month-end. The convention should be "
    "recorded consistently and not combined with a rate from a different market or definition."
)
add_text(
    doc,
    "Fourth, the predictive features should be subjected to multicollinearity assessment. Inflation, "
    "food index and exchange rate may contain strong trends or correlated movements, which can make "
    "individual coefficients unstable even when predictions are apparently useful. Fifth, a rolling "
    "back-test or expanding-window forecast evaluation could assess performance over more than one "
    "year. The fixed training period used for this first implementation produces only one contiguous "
    "out-of-sample trajectory. Sixth, a verification procedure should ensure that no test-period "
    "target leaks into the training data through derived lag or next-month columns."
)
add_text(
    doc,
    "Model adequacy should also be examined through residuals, pinball loss, prediction interval "
    "width, coverage by year and coverage by inflation regime. A coverage figure alone does not establish "
    "good calibration because an excessively broad band could attain coverage while providing little "
    "decision value. Quantile models should therefore be compared using both empirical coverage and "
    "interval sharpness."
)

add_heading(doc, "3.13 Ethical and Reproducibility Considerations", 1)
add_text(
    doc,
    "Economic forecasts may influence policy and investment decisions. Accordingly, results should "
    "be communicated as conditional model estimates with uncertainty rather than as guaranteed outcomes. "
    "The limitations of secondary and reconstructed data must be disclosed. The study also avoids "
    "fabricating values for missing observations in the final reported official series. Where interpolation "
    "is used temporarily, it must be clearly labelled and retained separately from the verified observations."
)
add_text(
    doc,
    "Reproducibility is supported by a versioned data file, a single executable Python programme, "
    "fixed random seeds where resampling is introduced, explicit file paths within a base directory, "
    "chronological split rules and exported prediction tables. A source-data register should accompany "
    "the final submission and record file names, source organisations, download dates, coverage periods "
    "and any transformations."
)

add_heading(doc, "3.14 Chapter Summary", 1)
add_text(
    doc,
    "This chapter explained the research methodology used to forecast next-month Nigerian inflation "
    "with quantile regression. Monthly observations were arranged in chronological order; next-month "
    "inflation was constructed as the forecast target; the period before January 2023 was used for "
    "training; and forecast origins from January 2023 to November 2025 were reserved for out-of-sample "
    "evaluation. The predictors were inflation lag, MPR, exchange rate and food index. Three separate "
    "quantile models were estimated at tau = 0.10, 0.50 and 0.90 (Koenker, 2005). The area between the lower and upper "
    "quantiles formed the nominal 80 percent prediction band."
)
add_text(
    doc,
    "The implementation produced 35 forecast observations and an empirical coverage rate of 25.71 "
    "percent in the current working dataset, which is materially below the nominal target. Rather than "
    "treating this result as proof of structural model failure, the programme and report identify it "
    "as a preliminary result requiring complete source-data verification. The required next methodological "
    "step is therefore to replace reconstructed observations with authoritative monthly records, rerun "
    "the fixed chronological evaluation and report coverage together with interval widths, calibration "
    "diagnostics and appropriate uncertainty."
)

add_heading(doc, "Appendix 3A: Principal Implementation and Output Files", 1)
add_table(
    doc,
    ["File", "Purpose"],
    [
        ["main.py", "Reads the monthly dataset, fits models, calculates coverage and creates the interactive graph."],
        ["nigeria_inflation_complete.csv", "Single compiled working dataset used by the implementation."],
        ["next_month_inflation_predictions.csv", "Contains forecast months, actuals, quantile forecasts and coverage indicators."],
        ["quantile_regression_coverage.csv", "Contains target coverage, test count and empirical coverage."],
        ["downloaded_data_sources.txt", "Records available source files and source links used during the data-compilation work."],
    ],
    [6.0, 8.7],
)

add_heading(doc, "References", 1)
for reference in [
    "Central Bank of Nigeria (2026) Monetary Policy Decisions and Exchange-rate Statistics. Available at: https://www.cbn.gov.ng (Accessed: 2 November 2026).",
    "Koenker, R. (2005) Quantile Regression. Cambridge: Cambridge University Press.",
    "Koenker, R. and Bassett, G. (1978) 'Regression quantiles', Econometrica, 46(1), pp. 33-50.",
    "Koenker, R. and Hallock, K.F. (2001) 'Quantile regression', Journal of Economic Perspectives, 15(4), pp. 143-156.",
    "National Bureau of Statistics (2026) NBS e-library. Available at: https://nigerianstat.gov.ng/elibrary (Accessed: 2 November 2026).",
    "Seabold, S. and Perktold, J. (2010) 'Statsmodels: Econometric and statistical modeling with Python', Proceedings of the 9th Python in Science Conference, pp. 92-96.",
]:
    ref = doc.add_paragraph()
    ref.add_run(reference)

add_heading(doc, "Appendix 3B: Academic Data-Source Note", 1)
add_text(
    doc,
    "Institutional sources identified in the project work include the National Bureau of Statistics "
    "e-library for CPI, inflation and food information; Central Bank of Nigeria monetary policy, "
    "exchange-rate and statistical publications for policy and exchange-rate data; and FRED for an "
    "optional Brent crude-oil series not used in the final required feature specification. Any source "
    "not directly verified against an original official publication should be documented as secondary "
    "or reconstructed in the final methodology and bibliography."
)

# Core properties
doc.core_properties.title = "Chapter Three: Research Methodology"
doc.core_properties.subject = "Predicting Inflation Bands for Nigeria Using Quantile Regression"
doc.core_properties.author = "Project Research Report"
doc.core_properties.keywords = "Nigeria, inflation, quantile regression, methodology, University of Ibadan"

# Footer page numbers
for section in doc.sections:
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("University of Ibadan - Research Project  |  ")
    run.font.size = Pt(9)

doc.save(OUTPUT_FILE)
print(OUTPUT_FILE)
