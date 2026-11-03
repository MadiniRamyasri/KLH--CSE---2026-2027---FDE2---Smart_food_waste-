const API = "http://127.0.0.1:8000";


let foodChart = null;
let trendChart = null;
let trendPageChart = null;


// =====================================================
// HELPER
// =====================================================

function setText(id, value) {

    const element =
        document.getElementById(id);

    if (element) {

        element.textContent = value;

    }

}


// =====================================================
// NAVIGATION
// =====================================================

function goToDashboard() {

    const dashboardButton =
        document.querySelector(
            '.nav-item[data-section="dashboard"]'
        );

    showSection(
        'dashboard',
        dashboardButton
    );

}


function showSection(
    sectionId,
    button
) {

    document
        .querySelectorAll(".section")
        .forEach(section => {

            section.classList.remove(
                "active-section"
            );

        });


    const section =
        document.getElementById(
            sectionId
        );


    if (section) {

        section.classList.add(
            "active-section"
        );

    }


    document
        .querySelectorAll(".nav-item")
        .forEach(item => {

            item.classList.remove(
                "active"
            );

        });


    if (button) {

        button.classList.add(
            "active"
        );

    }


    if (sectionId === "reports") {

        loadReports();

    }


    if (sectionId === "daily") {

        loadDailyPage();

    }


    if (sectionId === "predictions") {

        loadModelInfo();

    }

}


// =====================================================
// UPLOAD
// =====================================================

async function uploadDataset() {

    const fileInput =
        document.getElementById(
            "datasetFile"
        );

    const status =
        document.getElementById(
            "uploadStatus"
        );


    if (
        !fileInput.files ||
        fileInput.files.length === 0
    ) {

        status.textContent =
            "Please select a dataset first.";

        status.style.color =
            "red";

        return;

    }


    const formData =
        new FormData();


    formData.append(
        "file",
        fileInput.files[0]
    );


    status.textContent =
        "Uploading and processing dataset...";

    status.style.color =
        "#2563eb";


    try {

        const response =
            await fetch(
                `${API}/upload`,
                {
                    method: "POST",
                    body: formData
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data.detail
                )
            );

        }


        status.textContent =
             `✓ Uploaded successfully. ${data.records.toLocaleString()} records processed.`;

        status.style.color =
            "green";


        await initializeDashboard();

    }

    catch (error) {

        console.error(
            error
        );

        status.textContent =
            `Upload failed: ${error.message}`;

        status.style.color =
            "red";

    }

}


// =====================================================
// LOAD CITIES INTO ALL SELECTS
// =====================================================

async function loadCities() {

    try {

        const response =
            await fetch(
                `${API}/cities`
            );


        const data =
            await response.json();


        const selectIds = [

            "citySelect",
            "analysisCity",
            "trendCity",
            "predictCity",
            "recordCity"

        ];


        selectIds.forEach(id => {

            const select =
                document.getElementById(id);


            if (!select) return;


            const currentValue =
                select.value;


            select.innerHTML =
                `<option value="">Select City</option>`;


            data.cities.forEach(city => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    city;

                option.textContent =
                    city;

                select.appendChild(
                    option
                );

            });


            if (
                currentValue &&
                data.cities.includes(
                    currentValue
                )
            ) {

                select.value =
                    currentValue;

            }

        });

    }

    catch (error) {

        console.error(
            "Cities error:",
            error
        );

    }

}


// =====================================================
// LOAD FOODS
// =====================================================

async function loadFoods() {

    try {

        const response =
            await fetch(
                `${API}/foods`
            );


        const data =
            await response.json();


        const select =
            document.getElementById(
                "recordFood"
            );


        if (!select) return;


        select.innerHTML =
            `<option value="">Select Food</option>`;


        data.foods.forEach(food => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                food;

            option.textContent =
                food;

            select.appendChild(
                option
            );

        });

    }

    catch (error) {

        console.error(
            "Foods error:",
            error
        );

    }

}


// =====================================================
// DASHBOARD CITY CHANGE
// =====================================================

async function cityChanged() {

    const city =
        document.getElementById(
            "citySelect"
        ).value;


    if (!city) return;


    await Promise.all([

        loadAnalytics(city),

        loadFoodWaste(city),

        loadHighestWaste(city),

        loadWasteTrend(city),

        loadInsight(city),

        loadAnomalies(city),

        loadReductionTarget(city)

    ]);

}


// =====================================================
// ANALYTICS
// =====================================================

async function loadAnalytics(city) {

    try {

        const response =
            await fetch(
                `${API}/analytics/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        setText(
            "totalWaste",
            `${data.total_waste.toLocaleString()} kg`
        );


        setText(
            "totalPrepared",
            `${data.total_prepared.toLocaleString()} kg`
        );


        setText(
            "totalConsumed",
            `${data.total_consumed.toLocaleString()} kg`
        );


        setText(
            "wastePercentage",
            `${data.waste_percentage}%`
        );


        setText(
            "financialLoss",
            `₹${data.financial_loss.toLocaleString()}`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// FOOD CHART
// =====================================================

async function loadFoodWaste(city) {

    try {

        const response =
            await fetch(
                `${API}/waste-by-food/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        const canvas =
            document.getElementById(
                "foodChart"
            );


        if (foodChart) {

            foodChart.destroy();

        }


        foodChart =
            new Chart(
                canvas,
                {

                    type: "bar",

                    data: {

                        labels:
                            data.food,

                        datasets: [

                            {

                                label:
                                    "Waste (kg)",

                                data:
                                    data.waste,

                                borderWidth:
                                    1

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// HIGHEST FOOD
// =====================================================

async function loadHighestWaste(city) {

    try {

        const response =
            await fetch(
                `${API}/highest-waste/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        setText(
            "highestFood",
            data.food
        );


        setText(
            "highestFoodWaste",
            `${data.waste.toLocaleString()} kg`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DASHBOARD TREND
// =====================================================

async function loadWasteTrend(city) {

    try {

        const response =
            await fetch(
                `${API}/waste-trend/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        const canvas =
            document.getElementById(
                "trendChart"
            );


        if (trendChart) {

            trendChart.destroy();

        }


        trendChart =
            new Chart(
                canvas,
                {

                    type:
                        "line",

                    data: {

                        labels:
                            data.dates,

                        datasets: [

                            {

                                label:
                                    "Waste (kg)",

                                data:
                                    data.waste,

                                tension:
                                    0.3,

                                fill:
                                    false

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }
            );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DATA QUALITY
// =====================================================

async function loadDataQuality() {

    try {

        const response =
            await fetch(
                `${API}/data-quality`
            );


        const data =
            await response.json();


        setText(
            "dataQualityScore",
            `${data.score}%`
        );


        setText(
            "dataQualityDetails",

            `${data.rows.toLocaleString()} records • ${data.missing_values} missing • ${data.duplicate_records} duplicates`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DATASET SUMMARY
// =====================================================

async function loadDatasetSummary() {

    try {

        const response =
            await fetch(
                `${API}/dataset-summary`
            );


        const data =
            await response.json();


        setText(
            "datasetRows",
            data.rows.toLocaleString()
        );


        setText(
            "datasetCities",
            data.number_of_cities
        );


        setText(
            "datasetFoods",
            data.number_of_foods
        );


        setText(
            "datasetDateRange",

            `${data.date_min} → ${data.date_max}`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// ANOMALIES
// =====================================================

async function loadAnomalies(city) {

    try {

        const response =
            await fetch(
                `${API}/anomalies/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        setText(
            "anomalyCount",
            data.anomaly_count
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// REDUCTION TARGET
// =====================================================

async function loadReductionTarget(city) {

    try {

        const response =
            await fetch(
                `${API}/reduction-target/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        setText(
            "potentialReduction",

            `${data.potential_reduction.toLocaleString()} kg potential reduction`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DASHBOARD INSIGHT
// =====================================================

async function loadInsight(city) {

    try {

        const analyticsResponse =
            await fetch(
                `${API}/analytics/${encodeURIComponent(city)}`
            );


        const analytics =
            await analyticsResponse.json();


        const highestResponse =
            await fetch(
                `${API}/highest-waste/${encodeURIComponent(city)}`
            );


        const highest =
            await highestResponse.json();


        const anomalyResponse =
            await fetch(
                `${API}/anomalies/${encodeURIComponent(city)}`
            );


        const anomaly =
            await anomalyResponse.json();


        let level;


        if (
            analytics.waste_percentage >= 20
        ) {

            level =
                "High Waste Level";

        }

        else if (
            analytics.waste_percentage >= 10
        ) {

            level =
                "Moderate Waste Level";

        }

        else {

            level =
                "Low Waste Level";

        }


        setText(
            "insightLevel",
            level
        );


        setText(

            "insightText",

            `${city} has ${analytics.waste_percentage}% waste. ${highest.food} is the highest-waste food with ${highest.waste} kg. ${anomaly.anomaly_count} unusual observations were detected.`
        );


        let recommendation;


        if (
            analytics.waste_percentage >= 20
        ) {

            recommendation =
                `Reduce preparation quantities for ${highest.food}, review historical demand and investigate unusual waste observations.`;

        }

        else if (
            analytics.waste_percentage >= 10
        ) {

            recommendation =
                `Review consumption patterns for ${highest.food} and adjust future preparation quantities.`;

        }

        else {

            recommendation =
                `Continue monitoring preparation and consumption patterns to maintain the current waste level.`;

        }


        setText(
            "recommendation",
            recommendation
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// FOOD ANALYSIS PAGE
// =====================================================

async function loadFoodAnalysis() {

    const city =
        document.getElementById(
            "analysisCity"
        ).value;


    if (!city) return;


    try {

        const response =
            await fetch(
                `${API}/food-details/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        if (!data.length) return;


        const highest =
            data[0];


        setText(
            "analysisHighestFood",
            highest.Food
        );


        setText(
            "analysisHighestWaste",
            `${highest.Waste_kg.toLocaleString()} kg`
        );


        setText(
            "analysisWastePercentage",
            `${highest.Waste_Percentage}%`
        );


        let html = `

            <table>

                <thead>

                    <tr>

                        <th>Food</th>

                        <th>Prepared</th>

                        <th>Consumed</th>

                        <th>Waste</th>

                        <th>Waste %</th>

                        <th>Loss</th>

                    </tr>

                </thead>

                <tbody>
        `;


        data.forEach(row => {

            html += `

                <tr>

                    <td>${row.Food}</td>

                    <td>${row.Prepared_kg} kg</td>

                    <td>${row.Consumed_kg} kg</td>

                    <td>${row.Waste_kg} kg</td>

                    <td>${row.Waste_Percentage}%</td>

                    <td>₹${row.Cost_Loss.toLocaleString()}</td>

                </tr>

            `;

        });


        html += `

                </tbody>

            </table>
        `;


        document.getElementById(
            "foodTable"
        ).innerHTML = html;


        loadFoodRecommendations(
            city
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// RECOMMENDATIONS
// =====================================================

async function loadFoodRecommendations(
    city
) {

    try {

        const response =
            await fetch(
                `${API}/recommendations/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        renderRecommendations(
            "foodRecommendations",
            data.recommendations
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


function renderRecommendations(
    elementId,
    recommendations
) {

    const container =
        document.getElementById(
            elementId
        );


    if (
        !recommendations ||
        recommendations.length === 0
    ) {

        container.innerHTML =
            "No recommendations available.";

        return;

    }


    container.innerHTML =
        recommendations
        .map(item => `

            <div class="recommendation-item">

                <h3>
                    ${item.title}
                </h3>

                <p>
                    ${item.description}
                </p>

                <span class="priority">
                    Priority: ${item.priority}
                </span>

            </div>

        `)
        .join("");

}


// =====================================================
// TRENDS PAGE
// =====================================================

async function loadTrendPage() {

    const city =
        document.getElementById(
            "trendCity"
        ).value;


    if (!city) return;


    try {

        const response =
            await fetch(
                `${API}/waste-trend/${encodeURIComponent(city)}`
            );


        const data =
            await response.json();


        const waste =
            data.waste;


        if (waste.length === 0) return;


        const total =
            waste.reduce(
                (a, b) => a + b,
                0
            );


        const average =
            total / waste.length;


        const maxWaste =
            Math.max(
                ...waste
            );


        const maxIndex =
            waste.indexOf(
                maxWaste
            );


        setText(
            "averageWaste",
            `${average.toFixed(2)} kg`
        );


        setText(
            "highestWasteDay",
            data.dates[maxIndex]
        );


        const anomalyResponse =
            await fetch(
                `${API}/anomalies/${encodeURIComponent(city)}`
            );


        const anomaly =
            await anomalyResponse.json();


        setText(
            "trendAnomalies",
            anomaly.anomaly_count
        );


        const canvas =
            document.getElementById(
                "trendPageChart"
            );


        if (trendPageChart) {

            trendPageChart.destroy();

        }


        trendPageChart =
            new Chart(
                canvas,
                {

                    type:
                        "line",

                    data: {

                        labels:
                            data.dates,

                        datasets: [

                            {

                                label:
                                    "Daily Waste (kg)",

                                data:
                                    data.waste,

                                tension:
                                    0.3,

                                fill:
                                    false,

                                borderWidth:
                                    2

                            }

                        ]

                    },

                    options: {

                        responsive:
                            true,

                        maintainAspectRatio:
                            false,

                        scales: {

                            y: {

                                beginAtZero:
                                    true

                            }

                        }

                    }

                }
            );


        const recommendationResponse =
            await fetch(
                `${API}/recommendations/${encodeURIComponent(city)}`
            );


        const recommendations =
            await recommendationResponse.json();


        renderRecommendations(
            "trendRecommendations",
            recommendations.recommendations
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// MODEL INFORMATION
// =====================================================

async function loadModelInfo() {

    try {

        const response =
            await fetch(
                `${API}/model-info`
            );


        const data =
            await response.json();


        setText(
            "modelR2",
            data.r2_score
        );


        setText(
            "modelMAE",
            `${data.mae} kg`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// PREDICTION
// =====================================================

async function makePrediction() {

    const data = {

        City:
            document.getElementById(
                "predictCity"
            ).value,

        Hotel:
            document.getElementById(
                "predictHotel"
            ).value,

        Food:
            document.getElementById(
                "predictFood"
            ).value,

        Meal:
            document.getElementById(
                "predictMeal"
            ).value,

        Area:
            document.getElementById(
                "predictArea"
            ).value,

        Number_of_People:
            Number(
                document.getElementById(
                    "predictPeople"
                ).value
            ),

        Prepared_kg:
            Number(
                document.getElementById(
                    "predictPrepared"
                ).value
            )

    };


    const result =
        document.getElementById(
            "predictionResult"
        );


    try {

        result.textContent =
            "Calculating prediction...";


        const response =
            await fetch(
                `${API}/predict`,
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify(
                            data
                        )

                }
            );


        const prediction =
            await response.json();


        if (!response.ok) {

            throw new Error(
                prediction.detail
            );

        }


        result.innerHTML = `

            Predicted Waste:
            <strong>
                ${prediction.predicted_waste_kg} kg
            </strong>

        `;

    }

    catch (error) {

        result.textContent =
            `Prediction failed: ${error.message}`;

    }

}


// =====================================================
// REPORTS
// =====================================================

async function loadReports() {

    try {

        const qualityResponse =
            await fetch(
                `${API}/data-quality`
            );


        const quality =
            await qualityResponse.json();


        const summaryResponse =
            await fetch(
                `${API}/dataset-summary`
            );


        const summary =
            await summaryResponse.json();


        setText(
            "reportQuality",
            `${quality.score}%`
        );


        setText(
            "reportRecords",
            summary.rows.toLocaleString()
        );


        setText(
            "reportCities",
            summary.number_of_cities
        );


        setText(
            "reportFoods",
            summary.number_of_foods
        );


        const cityResponse =
            await fetch(
                `${API}/city-comparison`
            );


        const cities =
            await cityResponse.json();


        let html = `

            <table>

                <thead>

                    <tr>

                        <th>City</th>

                        <th>Waste</th>

                        <th>Prepared</th>

                        <th>Consumed</th>

                        <th>Waste %</th>

                        <th>Financial Loss</th>

                    </tr>

                </thead>

                <tbody>
        `;


        cities.forEach(city => {

            html += `

                <tr>

                    <td>${city.City}</td>

                    <td>${city.Total_Waste.toLocaleString()} kg</td>

                    <td>${city.Total_Prepared.toLocaleString()} kg</td>

                    <td>${city.Total_Consumed.toLocaleString()} kg</td>

                    <td>${city.Waste_Percentage}%</td>

                    <td>₹${city.Financial_Loss.toLocaleString()}</td>

                </tr>

            `;

        });


        html += `

                </tbody>

            </table>
        `;


        document.getElementById(
            "reportCityTable"
        ).innerHTML = html;

    }

    catch (error) {

        console.error(
            "Reports error:",
            error
        );

    }

}


// =====================================================
// DAILY RECORD
// =====================================================

function setTodayDate() {

    const now =
        new Date();


    const localDate =
        now.toISOString()
        .split("T")[0];


    const dateInput =
        document.getElementById(
            "recordDate"
        );


    if (
        dateInput &&
        !dateInput.value
    ) {

        dateInput.value =
            localDate;

    }


    updateRecordDay();

}


function updateRecordDay() {

    const date =
        document.getElementById(
            "recordDate"
        ).value;


    if (!date) {

        setText(
            "recordDay",
            "-"
        );

        return;

    }


    const day =
        new Date(
            `${date}T00:00:00`
        );


    setText(
        "recordDay",
        day.toLocaleDateString(
            "en-US",
            {
                weekday:
                    "long"
            }
        )
    );

}


function calculateLiveWaste() {

    const prepared =
        Number(
            document.getElementById(
                "recordPrepared"
            ).value
        ) || 0;


    const consumed =
        Number(
            document.getElementById(
                "recordConsumed"
            ).value
        ) || 0;


    const price =
        Number(
            document.getElementById(
                "recordPrice"
            ).value
        ) || 0;


    const waste =
        Math.max(
            prepared - consumed,
            0
        );


    const percentage =
        prepared > 0
            ? (
                waste
                /
                prepared
                *
                100
            )
            : 0;


    const loss =
        waste * price;


    setText(
        "liveWaste",
        `${waste.toFixed(2)} kg`
    );


    setText(
        "liveWastePercentage",
        `${percentage.toFixed(2)}%`
    );


    setText(
        "liveLoss",
        `₹${loss.toFixed(2)}`
    );

}


async function saveDailyRecord() {

    const date =
        document.getElementById(
            "recordDate"
        ).value;


    const city =
        document.getElementById(
            "recordCity"
        ).value;


    const food =
        document.getElementById(
            "recordFood"
        ).value;


    const prepared =
        Number(
            document.getElementById(
                "recordPrepared"
            ).value
        );


    const consumed =
        Number(
            document.getElementById(
                "recordConsumed"
            ).value
        );


    const people =
        Number(
            document.getElementById(
                "recordPeople"
            ).value
        );


    const price =
        Number(
            document.getElementById(
                "recordPrice"
            ).value
        ) || 0;


    const notes =
        document.getElementById(
            "recordNotes"
        ).value;


    const status =
        document.getElementById(
            "dailyStatus"
        );


    if (
        !date ||
        !city ||
        !food ||
        isNaN(prepared) ||
        isNaN(consumed) ||
        isNaN(people)
    ) {

        status.textContent =
            "Please fill all required fields.";

        status.style.color =
            "red";

        return;

    }


    if (
        consumed > prepared
    ) {

        status.textContent =
            "Consumed quantity cannot be greater than prepared quantity.";

        status.style.color =
            "red";

        return;

    }


    try {

        const response =
            await fetch(
                `${API}/daily-record`,
                {

                    method:
                        "POST",

                    headers: {

                        "Content-Type":
                            "application/json"

                    },

                    body:
                        JSON.stringify({

                            date:
                                date,

                            city:
                                city,

                            food:
                                food,

                            prepared_kg:
                                prepared,

                            consumed_kg:
                                consumed,

                            number_of_people:
                                people,

                            unit_price:
                                price,

                            notes:
                                notes

                        })

                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail
            );

        }


        status.textContent =
            "✓ Today's record saved successfully.";

        status.style.color =
            "green";


        document.getElementById(
            "recordPrepared"
        ).value = "";


        document.getElementById(
            "recordConsumed"
        ).value = "";


        document.getElementById(
            "recordPeople"
        ).value = "";


        document.getElementById(
            "recordNotes"
        ).value = "";


        calculateLiveWaste();

        await loadTodaySummary();

        await loadDailyHistory();

    }

    catch (error) {

        status.textContent =
            `Failed: ${error.message}`;

        status.style.color =
            "red";

    }

}


// =====================================================
// TODAY SUMMARY
// =====================================================

async function loadTodaySummary() {

    try {

        const response =
            await fetch(
                `${API}/today-summary`
            );


        const data =
            await response.json();


        const date =
            new Date(
                `${data.date}T00:00:00`
            );


        setText(
            "todayDate",
            data.date
        );


        setText(
            "todayDay",
            date.toLocaleDateString(
                "en-US",
                {
                    weekday:
                        "long"
                }
            )
        );


        setText(
            "todayPrepared",
            `${data.prepared.toLocaleString()} kg`
        );


        setText(
            "todayConsumed",
            `${data.consumed.toLocaleString()} kg`
        );


        setText(
            "todayWaste",
            `${data.waste.toLocaleString()} kg`
        );


        setText(
            "todayLoss",
            `₹${data.loss.toLocaleString()}`
        );

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DAILY HISTORY
// =====================================================

async function loadDailyHistory() {

    try {

        const response =
            await fetch(
                `${API}/daily-records`
            );


        const data =
            await response.json();


        const container =
            document.getElementById(
                "dailyHistory"
            );


        if (
            !data.records ||
            data.records.length === 0
        ) {

            container.innerHTML =
                "No records available.";

            return;

        }


        let html = `

            <table>

                <thead>

                    <tr>

                        <th>Date</th>

                        <th>Day</th>

                        <th>City</th>

                        <th>Food</th>

                        <th>Prepared</th>

                        <th>Consumed</th>

                        <th>Waste</th>

                        <th>Waste %</th>

                        <th>Loss</th>

                    </tr>

                </thead>

                <tbody>
        `;


        data.records
            .slice()
            .reverse()
            .forEach(record => {

                html += `

                    <tr>

                        <td>
                            ${record.Date}
                        </td>

                        <td>
                            ${record.Day}
                        </td>

                        <td>
                            ${record.City}
                        </td>

                        <td>
                            ${record.Food}
                        </td>

                        <td>
                            ${record.Prepared_kg} kg
                        </td>

                        <td>
                            ${record.Consumed_kg} kg
                        </td>

                        <td>
                            ${record.Waste_kg} kg
                        </td>

                        <td>
                            ${record.Waste_Percentage}%
                        </td>

                        <td>
                            ₹${Number(
                                record.Cost_Loss
                            ).toLocaleString()}
                        </td>

                    </tr>

                `;

            });


        html += `

                </tbody>

            </table>
        `;


        container.innerHTML =
            html;

    }

    catch (error) {

        console.error(
            error
        );

    }

}


// =====================================================
// DAILY PAGE
// =====================================================

async function loadDailyPage() {

    setTodayDate();

    await loadTodaySummary();

    await loadDailyHistory();

}


// =====================================================
// INPUT EVENTS
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const dateInput =
            document.getElementById(
                "recordDate"
            );


        if (dateInput) {

            dateInput.addEventListener(
                "change",
                updateRecordDay
            );

        }


        [

            "recordPrepared",
            "recordConsumed",
            "recordPrice"

        ].forEach(id => {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.addEventListener(
                    "input",
                    calculateLiveWaste
                );

            }

        });

    }
);


// =====================================================
// INITIALIZE
// =====================================================

async function initializeDashboard() {

    await loadCities();

    await loadFoods();

    await loadDataQuality();

    await loadDatasetSummary();

    setTodayDate();

}


document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);