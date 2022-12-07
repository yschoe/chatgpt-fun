/*
chatGPT fun by Yoonsuck Choe

Usage: 
1. Open a google doc.
2. Click [Extensions] -> [App Scripts]
3. In the new window, in the "Code.gs" file, copy and paste this file.
4. Click on [>Run]
5. Go back to your document and reload the page.
*. You need to approve access rights.

Note: I previously wrote a similar script for my personal use, so I was curious how chatGPT does it.

The prompt was: 

Write code in google app script for a custom menu that inserts a time stamp in US CST time zone into google doc. Insert the time stamp at the end of the document.

The explanation was: 

This Google App Script adds a custom menu called "Custom Menu" to the Google Docs user interface, with a menu item called "Insert Time Stamp". When the user selects this menu item, the insertTimeStamp() function is called. This function gets the current time in US CST time zone using the Session.getScriptTimeZone() method, and inserts the time stamp as a string at the end of the document using the appendText() method. This script is not particularly efficient or readable, but it does provide the basic functionality of creating a custom menu and inserting a time stamp in Google Docs.
*/

function onOpen() {
  // Add a custom menu to the Google Docs UI
  DocumentApp.getUi().createMenu('Custom Menu')
      .addItem('Insert Time Stamp', 'insertTimeStamp')
      .addToUi();
}

function insertTimeStamp() {
  // Get the current document
  var doc = DocumentApp.getActiveDocument();

  // Get the current time in US CST time zone
  var now = new Date();
  var timeZone = Session.getScriptTimeZone();
  var date = new Date(Utilities.formatDate(now, timeZone, "MM/dd/yyyy HH:mm:ss"));

  // Insert the time stamp at the end of the document
  var body = doc.getBody();
  var lastParagraph = body.getParagraphs().slice(-1)[0];
  lastParagraph.appendText('\n' + date.toString());
}
