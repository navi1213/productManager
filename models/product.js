const mongoose = require('mongoose');
//スキーマを定義
const productSchema = new mongoose.Schema({
    name:{
        type: String,
        required: true
    },
    price:{
        type: Number,
        required: true,
        min: 0
    },
    catergory:{
        type:String,
        enum:["果物","野菜","乳製品"]
    }
});
//モデルを作成(コレクションになる。コレクション名はproducts)
const Product = mongoose.model('Product', productSchema);

module.exports = Product;