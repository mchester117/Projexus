# Projexus Web App
#### Video Demo:  <URL HERE>
#### Description:
 This web application was designed for the metal fabrication company Projexus. The web application has several features to ease the burden of the day-to-day management of the company. Its primary function is a work-flow management system, allowing managers of the company to follow from initiation to completion the status of each of its custom ordered items. It also allows managers to do some book keeping tasks such as tracking how much clients owe the company, expected profits for each custom item, materials that need to be ordered, and how much the company is spending on materials.

## Functionality
When initiating the website, the first account needs to be created manually (for the purpose of this assignment, this has been done with username: a password: a). Once logged in, business managers will be able to see a snapshot of the quarter and any outstanding tasks. Right now, the outstanding tasks functionality is disabled and will be added in the future. (And since the ability to create employee accounts is currently disabled, so is the employee facing side of the website.)
After taking in the snapshot of the quarter, there are 2 navigation menus, one for managing the business and database, the other for sales.

### Manage
Within the manage menu, there are currently 2 options, the ability to view all materials used by the company, and the ability to purchase materials.
#### Materials
The materials page displays a list of materials and the associated cost for folding that material. From this page, the managers can edit the attributes of the materials, and add new materials. Per the design specifications of the company, inexperienced managers can use this page to get an idea of what folding a particular gauge of metal will cost, regardless of whether or not that particular metal has been used before, but it also allows the ability to affiliate customizable costs to each material. I've also added a gauge column leaning forward into a likely desire/requirement to be able to quickly change the price of all material with a particular gauge.
#### Purchase Materials
Once orders have been placed, managers will be able to use this page to quickly see what materials need to be purchased, how many, and for what individual items. Managers can update the entire "stack" of materials currently needed, or they can update materials for individual items to show that the materials have been purchased.

### Sales
Within the sales menu, there are currently 6 options, viewing a clients attributes, making a purchase with that client, selecting a different client, creating a new client, making a quick purchase, and working with invoices
#### Client
Selecting the current client will take the manager to the client page where they can view and edit contact information and the current attributes assigned to that client. They also can see the client's current outstanding balance, and the outstanding invoices associated with that balance. Finally, they can update any outstanding invoices to a "paid" status.

#### Select Client
Shows the manager a list of clients and allows the manager to select a client or create a new client

#### New Client
Allows the manager to add a new client and associate unique pricing values to the client, along with establishing contact information.

#### Order and Quick Order
Order and quick order are essentially the same, except quick order changes the current client to "quick order" a generic client for customers that are likely non-repeats or to prevent associating purchases with a particular client.
The order page allows the sales representative or manager to create line items for a client by entering several customizable attributes. As items are added to the cart, the sales associate is able to reuse attributes from the previous order, or clear the form for each new item. Once the cart is full/complete, the representative has the option to assign tax (as some customers are exempt) and to assign a delivery fee if desired. Upon completion of the order, the application then generates an invoice for the order, updates the database, and associates the invoice and cost with the client. If a client is just looking for a quote on a particular item, the associate can simply enter "0" for the quantity and still get the per unit price. This value will get added to the invoice so that the client can use it as an official quote for their superiors.

#### Invoices
The invoices page allows the manager to see all historic invoices and update the status of any invoice to paid. If desired, the manager can open the invoice to view it in detail. I considered a few options: only showing outstanding invoices, splitting the invoices into 2 tables separating by the status (outstanding/paid), and limiting the invoices to the quarter. I decided against all of these and went with the full table to allow the client maximum ability for collecting information.

## Files

### app.py
The actual application where most of the computation and database management is done. The brunt of the application is on the order page as it is the primary use of the application and has the most inputs to process. Due to the nature of the business and each piece being a custom piece, the pricing algorithm takes several lines of code. Additionally, it takes the inputs and converts them into easily readable formats for future use by the client, the employee that will create the piece, and by the sales associate to communicate with the client.

## projexus.db
The database that stores all of the information. It has been structured to primarily support invoicing and line item management, but also has some infrastructure to allow for easy integration of future-planned capabilities such as creating different levels of user accounts, tracking how payments were made, allowing the update of line items through the working process, and to allow for intuitive queries of the data base to pull desired information.

## README.md
This file

## render.py
A helper file that handles most of the html generation and database querying. As I was building the program, I realized I was passing long strings of variables to the html render function so I decided to use a function to render templates as opposed to using the standard render_template application inside the app.py file. I acknowledge a design flaw in that these long list of variables could actually be consolidated into objects, so in the future I will adjust the functions and parameters to allow for the ease of passing variables via an object.

## todo.txt
My todo list where I kept track of modules that needed to be completed, ideas I had for the website that were not requested by the end-user that I thought they'd like to consider, and any bugs/issues that I came across.

## Static Folder
 Inside the static folder is tye styles.css that apply styling the html, and some logo image files for later use. The styles.css is organized into sections: navbar, page headers, form controls, colors, and tables.

## Templates Folder
Contains all of the html templates used for rendering the web application. As my knowledge of javascript was light at the start of the project, I opted to keep the associated javascript for each page on its correpsonding html as opposed to creating a separate file for it. This forced me to regenerate and work the the functions and equations multiple times to develop a deeper understanding of the general structure of the language and the nuiances of reading and adjusting it for each situation.



