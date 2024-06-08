//シードデータを作成するファイル(expressやindex.jsとは別)
const mongoose = require('mongoose');
const Product = require('./models/product');

mongoose.connect('mongodb://localhost:27017/farmStand', {useNewUrlParser: true, useUnifiedTopology: true})
.then(() => {
    console.log("MongoDBコネクションOK!");
})
.catch(err => {
    console.log("MongoDBコネクションエラー");
    console.log(err);
});

// const p = new Product({
//     name:"リンゴ",
//     price:100,
//     catergory:"果物"
// });
// p.save().then(p => {
//     console.log(p);
// }).catch(e => {
//     console.log(e);
// });
const seedProduct = [
    {name:"ナス", price:98, catergory:"野菜"},
    {name:"キウイ", price:200, catergory:"果物"},
    {name:"キャベツ", price:300, catergory:"野菜"},
    {name:"牛乳", price:400, catergory:"乳製品"},
    {name:"卵", price:200, catergory:"乳製品"}
];
Product.insertMany(seedProduct)
.then(res => {
    console.log(res);
}).catch(e => {
    console.log(e);
});