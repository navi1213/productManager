const express = require('express');
const app = express();
const path = require('path');
const mongoose = require('mongoose');
const methodOverride = require('method-override');
const Product = require('./models/product');

mongoose.connect('mongodb://localhost:27017/farmStand', {useNewUrlParser: true, useUnifiedTopology: true})
.then(() => {
    console.log("MongoDBコネクションOK!");
})
.catch(err => {
    console.log("MongoDBコネクションエラー");
    console.log(err);
});

app.set("views", path.join(__dirname, 'views'));
app.set("view engine", "ejs");
app.use(express.urlencoded({extended:true}));
app.use(methodOverride('_method'));

const catergories = ["果物","野菜","乳製品","その他"];
// ルーティングを設定
//商品一覧画面のルーティング
app.get("/products", async(req, res) => {
    const {catergory} = req.query;
    if(catergory){
        const products = await Product.find({catergory});
        res.render("products/index", {products, catergory});
    }else{
        //時間がかかる処理なので非同期処理を使う
    const products = await Product.find({});
    res.render("products/index", {products,catergory:"全"});
    }
});
    
//商品新規登録画面のルーティング
app.get("/products/new", (req, res) => {
    res.render("products/new", {catergories});
});
//商品新規登録のPOSTリクエスト
app.post("/products", async(req, res) => {
    //受け取ったリクエストのbodyを使って新しい商品を作成
    //それを使ってproductモデルを使って新しいインスタンスを作成
    const newProduct = new Product(req.body);
    await newProduct.save();
    console.log(newProduct);
    res.redirect(`/products/${newProduct._id}`);
});
//商品詳細画面のルーティング
app.get("/products/:id",async(req, res) => {
    //idを取得
    const {id} = req.params;
    const product = await Product.findById(id);
    res.render("products/show", {product});
});
//商品編集画面のルーティング
app.get("/products/:id/edit", async(req, res) => {
    const {id} = req.params;
    const product = await Product.findById(id);
    res.render("products/edit", {product, catergories});
});

//商品編集のPUTリクエスト
//req.paramsはURLのパラメータを取得する。ここでは:idを取得している
app.put("/products/:id", async(req, res) => {
    const {id} = req.params;
    //非同期処理なのでawaitを使う
    const product = await Product.findByIdAndUpdate(id,req.body,{runValidators:true,new:true});
    res.redirect(`/products/${product._id}`);
});
//商品削除のDELETEリクエスト
app.delete("/products/:id",async(req, res) => {
    const {id} = req.params;
    const deletedProduct = await Product.findByIdAndDelete(id);
    res.redirect("/products");
    console.log(`削除された商品:${deletedProduct}`);
});

app.listen(3000, () => {
    console.log("ポート3000でサーバーを起動しました");
});