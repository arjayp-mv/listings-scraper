How does Axesso Amazon Review Scraper work?
The Axesso Amazon Review Scraper works seamlessly to extract detailed, real-time reviews directly from Amazon product pages. It is designed for efficiency and ease of use, requiring only a few parameters to deliver precise and comprehensive review data.

Here’s how it works:

Input Parameters: You simply provide the ASIN of the Amazon product page along with any additional filters, such as the desired number of reviews, Amazon domain and additional filters and sort options, optionally provided as a list..

Data Extraction: The Actor navigates to the product’s review section and extracts all relevant details, including star ratings, review titles, full descriptions, customer reactions (e.g., helpful votes), review dates, and any attached images.

Real-Time Output: Unlike cached or preprocessed data, our scraper retrieves up-to-date reviews directly from Amazon. This ensures the results are always fresh and reliable.

Download Options: Once the reviews are extracted, the data can be downloaded in your preferred format, such as JSON, CSV, Excel, XML, or HTML.

With Axesso Amazon Review Scraper, you get an easy-to-use, robust tool that ensures fast, accurate, and flexible data extraction for your specific needs.

Input data
The Axesso Amazon Review Scraper accepts input in JSON format. The provided JSON include one mandatory JSON Array field "input" with the following fields:

asin (Required) The Amazon Standard Identification Number of the product whose reviews you want to scrape.
domainCode (Required) The Amazon marketplace domain code (e.g., "com" for Amazon.com, "de" for Amazon Germany).
sortBy (Optional) The sorting method for reviews. Options include "recent" for the most recent reviews or "helpful" for the most helpful ones.
maxPages (Optional) Set the maximum number of review pages to scrape. For instance, "1" limits scraping to the first page. Max value is 10 pages as this is predefined limit by Amazon. Default value is 1.
filterByStar (Optional) Filter reviews by star rating, such as "five_star" to scrape only 5-star reviews.
filterByKeyword (Optional) Filter reviews containing specific keywords, such as "good" to target relevant content.
reviewerType (Optional) Specify whether to include all reviews ("all_reviews") or only verified purchase reviews ("verified_reviews").
formatType (Optional) Select the review format to scrape. "current_format" captures the latest review layout on Amazon.
mediaType (Optional) Choose the type of content to include, such as "all_contents" to fetch text and media or "media_reviews_only" for image and video reviews only.
The 'input' field is an array, allowing you to pass multiple ASINs in one run. Each ASIN can be configured with individual filters and options, enabling the scraping of up to millions of reviews in a single run.

Here an example of a sample input:

{
"input": [
    {
    "asin": "B08C1W5N87",
    "domainCode": "com",
    "sortBy": "recent",
    "filterByStar": "four_star",
    "maxPages": 1
    },
    {
    "asin": "B09G7ZMVJP",
    "domainCode": "de",
    "sortBy": "helpful",
    "maxPages": 1
    },
    {
    "asin": "B086K4ZMT3",
    "domainCode": "co.uk",
    "sortBy": "recent",
    "maxPages": 1,
    "filterByKeyword": "good"

    }
]
}

Output data
[
    {
        "statusCode": 200,
        "statusMessage": "FOUND",
        "asin": "B086K4ZMT3",
        "productTitle": "Knipex Cobra® XS Pipe Wrench and Water Pump Pliers grey atramentized, embossed, rough surface 100 mm (self-service card/blister) 87 00 100 BK",
        "currentPage": 1,
        "sortStrategy": "recent",
        "countReviews": 17,
        "domainCode": "co.uk",
        "filters": {
            "filterByKeyword": "good"
        },
        "countRatings": 17,
        "productRating": "4.8 out of 5",
        "reviewSummary": {
            "fiveStar": {
                "percentage": 87
            },
            "fourStar": {
                "percentage": 10
            },
            "threeStar": {
                "percentage": 2
            },
            "twoStar": {
                "percentage": 0
            },
            "oneStar": {
                "percentage": 1
            }
        },
        "reviewId": "RIGZGOCR0K67Y",
        "text": "Awesome small-small pliers. But good enough for most jobs when camping or adjusting bikes or anything in emergency.",
        "date": "Reviewed in the United Kingdom on 24 November 2024",
        "rating": "5.0 out of 5 stars",
        "title": "Great little pliers. Keep in my EDC.",
        "userName": "A. Ross",
        "numberOfHelpful": 0,
        "variationId": "B086K4ZMT3",
        "imageUrlList": null,
        "variationList": [
            "Style Name: Single"
        ],
        "locale": null,
        "verified": true,
        "vine": false,
        "videoUrlList": [],
        "profilePath": "/gp/profile/amzn1.account.AECUH4WABG5YYRHL7NBU7YZPGHWA/ref=cm_cr_arp_d_gw_btm"
    }
]

Valid Domains
The following domain codes are currently supported by this Actor:

"com" for Amazon USA
"ca" for Amazon Canada
"co.uk" for Amazon United Kingdom
"in" for Amazon India
"de" for Amazon Germany
"fr" for Amazon France
"it" for Amazon Italy
"es" for Amazon Spain
"co.jp" for Amazon Japan
"com.au" for Amazon Australia
"com.br" for Amazon Brazil
"nl" for Amazon Netherlands
"se" for Amazon Sweden
"com.mx" for Amazon Mexico
"ae" for Amazon United Arab Emirates
How much does Axesso Amazon Reviews Scraper cost?
Estimating the resources required for data scraping can be difficult due to the diverse nature of use cases. Therefore, it is advisable to conduct a test scrape using a small sample of input data and generate a limited amount of output. This will allow you to determine the cost per scrape, which can then be multiplied by the total number of scrapes you plan to perform.

What to consider when using this Actor?
Axesso - Data Service is performing Web Crawling activities for over a decade. All our expertises are included in this Actor, this means the user of this Actor is not required to deal with any inconveniences of web scraping.

In details it means we cover the whole lifecycle including

Proxy Rotation: We Use our own Proxy Pool including several million proxies in all countries worldwide avoiding that our Scraper can be blocked.

Geo Targeting: We determine the correct location based on the provided URL. If you would like to fetch result for amazon.com domain, we only use Proxies from USA for the corresponding request. Thus, we support all Amazon domains available while using always the right Proxy location.

Captchas and 503 Status Code: Captchas and temporary blocks are completely handled by this Actor under the hood ensuring the user to get always the required data.

Further rotation As already mentioned, our Actor is covering all required activities to ensure a smooth user experience at any point in time.

Where else you can find Axesso - Data Service solutions?
Our solutions are available and distributed via different channels. You can find our full API selection either on own API Portal or on Rapid API.

You can find more information about our Amazon API on our product page.

On RapidAPI our solutions are already available since 5 years proven by a track record of over 5,000 subscribers across all our APIs. Check it out, to gain trust in our experience!

API Clients
from apify_client import ApifyClient

# Initialize the ApifyClient with your API token
client = ApifyClient("<YOUR_API_TOKEN>")

# Prepare the Actor input
run_input = { "input": [{
            "asin": "B08C1W5N87",
            "domainCode": "com",
            "sortBy": "recent",
            "maxPages": 1,
            "filterByStar": "five_star",
            "filterByKeyword": "good",
            "reviewerType": "all_reviews",
            "formatType": "current_format",
            "mediaType": "all_contents",
        }] }

# Run the Actor and wait for it to finish
run = client.actor("ZebkvH3nVOrafqr5T").call(run_input=run_input)

# Fetch and print Actor results from the run's dataset (if there are any)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item)


Run Actor
View API reference
Runs this Actor. The POST payload including its Content-Type header is passed as INPUT to the Actor (typically application/json). The Actor is started with the default options; you can override them using various URL query parameters.

POST
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/runs?token=***


Hint: By adding the method=POST query parameter, this API endpoint can be called using a GET request and thus used in third-party webhooks.

Run Actor synchronously and get a key-value store record
View API reference
Runs this Actor and waits for it to finish. The POST payload, including its Content-Type, is passed as Actor input. The OUTPUT record (or any other specified with the outputRecordKey query parameter) from the default key-value store is returned as the HTTP response. The Actor is started with the default options; you can override them using various URL query parameters. Note that long HTTP connections might break.

POST
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/run-sync?token=***


Hint: This endpoint can be used with both POST and GET request methods, but only the POST method allows you to pass input.

Run Actor synchronously and get dataset items
View API reference
Runs this Actor and waits for it to finish. The POST payload including its Content-Type header is passed as INPUT to the Actor (usually application/json). The HTTP response contains the Actor's dataset items, while the format of items depends on specifying dataset items' format parameter.

POST
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/run-sync-get-dataset-items?token=***


Hint: This endpoint can be used with both POST and GET request methods, but only the POST method allows you to pass input.

Get Actor
View API reference
Returns settings of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper?token=***



Test endpoint

Get a list of Actor versions
View API reference
Returns a list of versions of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/versions?token=***



Test endpoint

Get a list of Actor webhooks
View API reference
Returns a list of webhooks of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/webhooks?token=***



Test endpoint

Update Actor
View API reference
Updates settings of this Actor. The POST payload must be a JSON object with fields to update.

PUT
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper?token=***


Update Actor version
View API reference
Updates version of this Actor. Replace the 0.0 with the updating version number. The POST payload must be a JSON object with fields to update.

PUT
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/versions/0.0?token=***


Delete Actor
View API reference
Deletes this Actor and all associated data.

DELETE
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper?token=***


Get a list of builds
View API reference
Returns a list of builds of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/builds?token=***



Test endpoint

Build Actor
View API reference
Builds a specific version of this Actor and returns information about the build. Replace the 0.0 parameter with the desired version number.

POST
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/builds?token=***&version=0.0


Hint: By adding the method=POST query parameter, this API endpoint can be called using a GET request and thus used in third-party webhooks.

Get a list of runs
View API reference
Returns a list of runs of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/runs?token=***



Test endpoint

Get last run
View API reference
Returns the last run of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/runs/last?token=***



Test endpoint

Hint: Add the status=SUCCEEDED query parameter to only get the last successful run of the Actor.

Get last run dataset items
View API reference
Returns data from the default dataset of the last run of this Actor in JSON format.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/runs/last/dataset/items?token=***



Test endpoint

Hint: Add the status=SUCCEEDED query parameter to only get the last successful run of the Actor. This API endpoint supports all the parameters of the Dataset Get Items endpoint.

Get OpenAPI definition
View API reference
Returns the OpenAPI definition for the Actor's default build with information on how to run this Actor build using the API.

GET
https://api.apify.com/v2/acts/axesso_data~amazon-reviews-scraper/builds/default/openapi.json


Test endpoint

