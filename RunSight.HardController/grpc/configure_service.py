"""
ConfigureService 实现
"""
import grpc
from concurrent import futures
import logging
from typing import Any

from grpc_gen.Protobuf.Services import ConfigureService_pb2_grpc
from grpc_gen.Protobuf.Requests import ConfigureUpdateReq_pb2
from grpc_gen.Protobuf.Responses import ConfigureUpdateRsp_pb2
from grpc_gen.Protobuf.Enums import RetCodes_pb2

class ConfigureServicer(ConfigureService_pb2_grpc.ConfigureServiceServicer):
    """ConfigureService 实现类"""
    
    def UpdateConfigure(self, request: ConfigureUpdateReq_pb2.ConfigureUpdateReq, context: Any) -> ConfigureUpdateRsp_pb2.ConfigureUpdateRsp:
        """
        更新配置
        
        Args:
            request: 配置更新请求
            context: gRPC 上下文
            
        Returns:
            配置更新响应
        """
        try:
            # TODO: 实现配置更新逻辑
            configure = request.Configure
            logging.info(f"Received configure update request: {configure}")
            
            # 返回成功响应
            return ConfigureUpdateRsp_pb2.ConfigureUpdateRsp(
                RetCode=RetCodes_pb2.RetCodes.Success,
                Message="配置更新成功"
            )
        except Exception as e:
            logging.error(f"Failed to update configure: {e}")
            return ConfigureUpdateRsp_pb2.ConfigureUpdateRsp(
                RetCode=RetCodes_pb2.RetCodes.Failed,
                Message=f"配置更新失败：{str(e)}"
            )

def serve():
    """启动 gRPC 服务器"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    ConfigureService_pb2_grpc.add_ConfigureServiceServicer_to_server(
        ConfigureServicer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logging.info("ConfigureService server started on port 50051")
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    serve() 