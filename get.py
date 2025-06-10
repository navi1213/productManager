import json
import boto3
import base64
import logging

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = "sdrp-us"
DIRECTORY = "furushima-tmp/"

s3 = boto3.resource("s3")
bucket = s3.Bucket(BUCKET_NAME)

def lambda_handler(event, context):
    try:
        logger.info("=== EVENT ===")
        logger.info(json.dumps(event, default=str))
        
        # CORS ヘッダー
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,x-filename,Authorization",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
            "Content-Type": "application/json"
        }
        
        # OPTIONSリクエスト（プリフライト）の処理
        if event.get('httpMethod') == 'OPTIONS':
            return {
                "statusCode": 200,
                "headers": headers,
                "body": ""
            }
        
        # リクエストの処理方式を判定
        content_type = event.get('headers', {}).get('Content-Type', '').lower()
        
        if content_type == 'application/json':
            # 方式1: JSON形式（既存のロジック）
            if "body" in event:
                body = json.loads(event["body"])
            elif "body-json" in event:
                body = event["body-json"]
            else:
                raise ValueError("Missing 'body' in event")
            
            filename = body["filename"]
            filedata = base64.b64decode(body['filedata'])
            
        elif event.get('isBase64Encoded', False):
            # 方式2: バイナリデータ直接送信
            filedata = base64.b64decode(event['body'])
            filename = event.get('headers', {}).get('x-filename', 'uploaded_file')
            
        else:
            # 方式3: テキストとして送信されたバイナリデータ
            filedata = event['body'].encode('utf-8')
            filename = event.get('headers', {}).get('x-filename', 'uploaded_file')
        
        # ファイルサイズチェック
        if len(filedata) > 10 * 1024 * 1024:  # 10MB制限
            raise ValueError("ファイルサイズが10MBを超えています")
        
        # S3にアップロード
        s3_key = DIRECTORY + filename
        
        bucket.put_object(
            Body=filedata, 
            Key=s3_key,  # 修正: key → Key
            ServerSideEncryption='AES256'
        )
        
        logger.info(f"アップロード成功: {s3_key}")
        
        return {
            "statusCode": 200,
            "headers": headers,
            "body": json.dumps({
                "message": "アップロード成功",
                "filename": filename,
                "s3_key": s3_key,
                "size": len(filedata)
            }, ensure_ascii=False)
        }
        
    except ValueError as e:
        logger.error(f"バリデーションエラー: {str(e)}")
        return {
            "statusCode": 400,
            "headers": headers,
            "body": json.dumps({
                "error": str(e)
            }, ensure_ascii=False)
        }
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}")
        return {
            "statusCode": 500,
            "headers": headers,
            "body": json.dumps({
                "error": "内部サーバーエラー"
            }, ensure_ascii=False)
        }
