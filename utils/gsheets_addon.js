function Initialize() {
  try {

    var triggers = ScriptApp.getProjectTriggers();

    for (var i in triggers)
      ScriptApp.deleteTrigger(triggers[i]);

    ScriptApp.newTrigger("SubmitGoogleSheetsData")
      .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
      .onEdit()
      .create();

  } catch (error) {
    throw new Error("Please add this code in the Google Spreadsheet");
  }
}

function SubmitGoogleSheetsData(e) {

  if (!e) {
    throw new Error("Please go the Run menu and choose Initialize");
  }

  try {

    payload_tmp = buildPayloadFromSpreadsheet();
    payload = {"shoppinglist_items" : payload_tmp}

    var POST_SHOPITEM_URL = "https://django-cloudrun-equcscffbq-ew.a.run.app//shoppinglist/";

    headers = {
      'Content-Type': 'application/json',
      'Authorization': 'Token  15f2d1616011119dfb6db4dcf47656fd0af6b4d2'
    }

    var options = {
      'method': 'post',
      "contentType" : "application/json",
      'headers': headers,
      'payload': JSON.stringify(payload),
      'muteHttpExceptions': false
    }
    Logger.log(options.payload);

    var response = UrlFetchApp.fetch(POST_SHOPITEM_URL, options);
    Logger.log(JSON.stringify(response));

  } catch (error) {
    Logger.log(error.toString());
  }
}

function buildPayloadFromSpreadsheet(){
  var
    activeSheet = SpreadsheetApp.getActiveSheet();
    lastRow = activeSheet.getLastRow();
    allItemsCell = activeSheet.getRange(lastRow, 3, 1, 1).getValue();
    allItemsList = allItemsCell.split("Nome:")

    let fieldsPerItem = {};
    for(let i=1;i <= allItemsList.length-1;i++){
      if (allItemsList[i] != "") {
          fieldsPerItem[i] = allItemsList[i];
      }
    }
    let payloads = [];
    let expectedPrice = "";
    for(var key in fieldsPerItem){
      let line = fieldsPerItem[key];
      let start = line.indexOf(" Preço Limite:");
      let end = line.indexOf(", Mercado");
      let sliced = fieldsPerItem[key].slice(start+14,end);
      let newline = "";
      if (sliced != " "){
        let expectedPriceSliced = sliced.replace(",",".").trim();
        let expectedPriceTmp = Number(expectedPriceSliced)
        if (typeof expectedPriceTmp == "number"
            && expectedPriceTmp != 0
            && !isNaN(expectedPriceTmp))
        {
          expectedPrice = expectedPriceTmp;
        }
        newline = line.replace(sliced,expectedPrice)
        entries = newline.split(",");
      }else{
        sliced = fieldsPerItem[key].slice(start,end+1);
        newline = line.replace(sliced," ")
        entries = newline.split(",");
      }
      let fields = [];
      let payload = {};
      for(let i=0;i <= entries.length-1;i++){
        fields.push(entries[i].slice(entries[i].indexOf(':')+1).trim())
      }

      payload = {
          "item_name": fields[0],
          "item_brand": fields[1],
          "item_quantity": fields[2],
          "shoppinglist_id": "1"
      }

      if (expectedPrice.length != ""){
        payload["expected_item_price_max"] = fields[3];
        payload["item_grocery_store"] = fields[4];
      }else{
        payload["item_grocery_store"] = fields[3];
      }
      payloads.push(payload);
      payload = [];
    }
    return payloads;
}