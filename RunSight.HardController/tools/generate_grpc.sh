#!/bin/bash

# 设置目录
PROTOBUF_DIR="../RunSightConfigureClientAndroid/RunSight.Shared/Protobuf/"
OUTPUT_DIR="../grpc_gen"

# 确保输出目录存在
mkdir -p $OUTPUT_DIR

# 遍历所有 .proto 文件
for proto_file in $(find $PROTOBUF_DIR -name "*.proto"); do
    echo "正在处理: $proto_file"
    
    # 生成 Python 代码
    python -m grpc_tools.protoc \
        -I $PROTOBUF_DIR/.. \
        --python_out=$OUTPUT_DIR \
        --pyi_out=$OUTPUT_DIR \
        --grpc_python_out=$OUTPUT_DIR \
        $proto_file
    
    if [ $? -eq 0 ]; then
        echo "成功生成: $proto_file"
    else
        echo "生成失败: $proto_file"
    fi
done

echo "所有 .proto 文件处理完成"