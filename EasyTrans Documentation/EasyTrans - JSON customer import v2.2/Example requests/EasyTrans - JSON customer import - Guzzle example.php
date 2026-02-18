<?php
/*********************************************************************************
EasyTrans Software B.V.
Web: www.easytrans.nl / www.easytrans.co.uk
Mail: info@easytrans.nl / info@easytrans.co.uk
Phone: +31 85 0479 475 / +44 20 3966 3373

Description: Example of the use of the JSON customer import API using the Guzzle PHP HTTP client

*********************************************************************************/
header('Content-Type: application/json');

// Use Composer to install Guzzle
require 'vendor/autoload.php';

//// Example customer JSON data ////
// Contact within the customer
$customer_contacts[] = [
	'salutation' => 1,
	'contact_name' => 'Bram Pietersen',
	'telephone' => '020-7654321',
	'mobile' => '06-12345678',
	'email' => 'bram@easytrans.nl',
	'use_email_for_invoice' => true,
	'use_email_for_reminder' => true,
	'contact_remark' => 'Warehouse manager',
];

// Customer
$customers[] = [
	'company_name' => 'Example Company A',
	'attn' => 'Administration',
	'address' => 'Keizersgracht',
	'houseno' => '1a',
	'address2' => '2nd floor',
	'postal_code' => '1015CC',
	'city' => 'Amsterdam',
	'country' => 'NL',
	'mail_address' => 'Postbus',
	'mail_houseno' => '73',
	'mail_postal_code' => '1010AA',
	'mail_city' => 'Amsterdam',
	'mail_country' => 'NL',
	'website' => 'www.easytrans.nl',
	'remark' => 'Customer remark',
	'ibanno' => 'NL63INGB0004511811',
	'bicno' => 'INGBNL2A',
	'bankno' => '4511811',
	'uk_sort_code' => '12-34-56',
	'cocno' => '50725769',
	'vatno' => 'NL822891682B01',
	'eorino' => 'NL822891682',
	'vat_liable' => 1,
	'customer_contacts' => $customer_contacts,
];

// JSON request
$jsonRequest = [
	'authentication' => [
		'username' => 'user1234',
		'password' => 'abcd1234',
		'type' => 'customer_import',
		'mode' => 'test'
	],
	'customers' => $customers
];

// Send request to the API
$client = new GuzzleHttp\Client(['base_uri' => 'https://www.mytrans.nl/demo/import_json.php', 'timeout' => 10]);
$response = $client->post('', ['json' => $jsonRequest]);

echo $response->getBody();
