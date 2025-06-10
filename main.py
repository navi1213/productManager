import json
import boto3
import os
import logging
from datetime import datetime, timedelta
from botocore.exceptions import ClientError
import re
import uuid

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3クライアントの初期化
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    署名付きURL生成のメインハンドラー
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # CORS ヘッダー
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'POST,OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # プリフライトリクエスト（OPTIONS）の処理
    if event.get('httpMethod') == 'OPTIONS':
        logger.info("Handling OPTIONS preflight request")
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # リクエストボディの解析
        if not event.get('body'):
            raise ValueError('リクエストボディが空です')
        
        try:
            request_data = json.loads(event['body'])
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            raise ValueError('リクエストボディが正しいJSON形式ではありません')
        
        # 必須パラメータの取得
        file_name = request_data.get('fileName')
        file_type = request_data.get('fileType')
        file_size = request_data.get('fileSize')
        
        logger.info(f"Request data: fileName={file_name}, fileType={file_type}, fileSize={file_size}")
        
        # 入力値検証
        validate_input(file_name, file_type, file_size)
        
        # ユニークなS3キーの生成
        s3_key = generate_unique_key(file_name)
        
        # 署名付きURL生成
        upload_url = generate_presigned_url(s3_key, file_type, file_size)
        
        # レスポンス作成
        response_body = {
            'uploadUrl': upload_url,
            'key': s3_key,
            'bucket': os.environ['S3_BUCKET_NAME'],
            'expires': int((datetime.utcnow() + timedelta(minutes=5)).timestamp() * 1000)  # ミリ秒
        }
        
        logger.info(f"Generated presigned URL for key: {s3_key}")
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_body, ensure_ascii=False)
        }
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({
                'error': str(e)
            }, ensure_ascii=False)
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': '署名付きURL生成に失敗しました'
            }, ensure_ascii=False)
        }

def validate_input(file_name, file_type, file_size):
    """
    入力値の検証
    """
    # 必須項目チェック
    if not file_name or not file_type:
        raise ValueError('ファイル名とファイルタイプは必須です')
    
    # ファイル名の検証
    if len(file_name) > 255:
        raise ValueError('ファイル名が長すぎます（255文字以内）')
    
    # 危険な文字のチェック
    dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
    if any(char in file_name for char in dangerous_chars):
        raise ValueError('ファイル名に使用できない文字が含まれています')
    
    # ファイルサイズ制限
    max_size = 100 * 1024 * 1024  # 100MB
    if file_size and file_size > max_size:
        raise ValueError(f'ファイルサイズが制限({max_size // 1024 // 1024}MB)を超えています')
    
    # 許可されるMIMEタイプ
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain', 'text/csv'
    ]
    
    if file_type not in allowed_types:
        raise ValueError('許可されていないファイル形式です')

def generate_unique_key(file_name):
    """
    ユニークなS3キーを生成
    """
    # タイムスタンプとUUIDを使用
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]
    
    # ファイル名のサニタイズ
    sanitized_name = re.sub(r'[^a-zA-Z0-9._-]', '_', file_name)
    
    # S3キーの生成（フォルダ構造を含む）
    return f"uploads/{timestamp}_{unique_id}_{sanitized_name}"

def generate_presigned_url(s3_key, file_type, file_size):
    """
    署名付きURLの生成
    """
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    # 署名付きURLのパラメータ
    params = {
        'Bucket': bucket_name,
        'Key': s3_key,
        'ContentType': file_type,
        'ServerSideEncryption': 'AES256',
        'Metadata': {
            'original-name': s3_key.split('_')[-1],  # 元のファイル名
            'upload-timestamp': datetime.utcnow().isoformat(),
            'file-size': str(file_size) if file_size else 'unknown'
        }
    }
    
    try:
        # 署名付きURL生成（5分間有効）
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params=params,
            ExpiresIn=300  # 5分
        )
        
        return presigned_url
        
    except ClientError as e:
        logger.error(f"S3 client error: {e}")
        raise Exception('S3署名付きURL生成に失敗しました')
