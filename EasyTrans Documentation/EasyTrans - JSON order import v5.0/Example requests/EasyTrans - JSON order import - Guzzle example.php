<?php
/*********************************************************************************
EasyTrans Software B.V.
Web: www.easytrans.nl / www.easytrans.co.uk
Mail: info@easytrans.nl / info@easytrans.co.uk
Phone: +31 85 0479 475 / +44 20 3966 3373

Description: Example of the use of the JSON order import API using the Guzzle PHP HTTP client

*********************************************************************************/
header('Content-Type: application/json');

// Use Composer to install Guzzle
require 'vendor/autoload.php';

//// Example order JSON data ////
// Pickup destination
$order_destinations[] = [
   'collect_deliver' => 0,
   'company_name' => 'Example Company A',
   'contact' => 'Mr. Johnson',
   'address' => 'Keizersgracht',
   'houseno' => '1a',
   'address2' => '2nd floor',
   'postal_code' => '1015CC',
   'city' => 'Amsterdam',
   'country' => 'NL',
   'telephone' => '020-1234567',
   'destination_remark' => 'Call before arrival',
   'customer_reference' => '',
   'delivery_date' => date('Y-m-d'),
   'delivery_time' => '12:00',
   'delivery_time_from' => '08:00',
];

// Delivery destination
$order_destinations[] = [
   'collect_deliver' => 1,
   'company_name' => 'Example company B',
   'contact' => 'Mr. Pietersen',
   'address' => 'Kanaalweg',
   'houseno' => '14',
   'address2' => '',
   'postal_code' => '3526KL',
   'city' => 'Utrecht',
   'country' => 'NL',
   'telephone' => '030-7654321',
   'destination_remark' => 'Delivery at neighbours if not at home',
   'customer_reference' => 'ABCD1234',
   'delivery_date' => date('Y-m-d'),
   'delivery_time' => '17:00',
   'delivery_time_from' => '15:00',
];

// Goods to be transported
$order_packages[] = [
   'amount' => 2,
   'weight' => 150,
   'length' => 120,
   'width' => 80,
   'height' => 50,
   'description' => 'Euro pallet'
];
$order_packages[] = [
   'amount' => 3,
   'weight' => 15,
   'description' => 'Boxes with folders'
];

// Order
$orders[] = [
   'date' => date('Y-m-d'),
   'time' => date('H:i'),
   'status' => 'submit',
   'productno' => 2,
   'remark' => '1 Euro pallet and 3 boxes',
   'remark_invoice' => 'P/O Number: ABCD1234',
   'email_receiver' => '',
   'order_destinations' => $order_destinations,
   'order_packages' => $order_packages,
];

// JSON request
$jsonRequest = [
   'authentication' => [
      'username' => 'user1234',
      'password' => 'abcd1234',
      'type' => 'order_import',
      'mode' => 'test',
      'return_rates' => false,
      'return_documents' => true,
      'version' => 2,
   ],
   'orders' => $orders
];

// Send request to the API
$client = new GuzzleHttp\Client(['base_uri' => 'https://www.mytrans.nl/demo/import_json.php', 'timeout' => 10]);
$response = $client->post('', ['json' => $jsonRequest]);

echo $response->getBody();
