using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Grpc.Core;
using Microsoft.Extensions.Logging;
using RunSightConfigureClient.Models;

namespace RunSightConfigureClient.Services;

public class DeviceConnectionService(ILogger<DeviceConnectionService> logger)
{
    public ILogger<DeviceConnectionService> Logger { get; } = logger;
    
    public DeviceConnectionInfo? CurrentConnectedDevice { get; private set; }

    public DeviceConfigure CurrentDeviceConfigure { get; set; } = new();

    public Uri? BaseUrl { get; private set; } 
    
    public async Task ConnectToNewDevice(DeviceConnectionInfo info)
    {
        try
        {
            var uri = new UriBuilder()
            {
                Host = info.DeviceAddress,
                Port = info.DevicePort,
                Scheme = "http"
            }.Uri;
            BaseUrl = uri;
            var httpClient = new HttpClient();
            var json = await httpClient.GetAsync(new UriBuilder(uri)
            {
                Path = "configure"
            }.Uri);
            CurrentDeviceConfigure = JsonSerializer.Deserialize<DeviceConfigure>(await json.Content.ReadAsStringAsync())!;
        }
        catch (Exception e)
        {
            Logger.LogError(e, "无法连接到设备");
            throw;
        }
    }

    public void DisconnectFromCurrentDevice()
    {
        CurrentConnectedDevice = null;
    }
    
    public async Task UploadSettings()
    {
        try
        {
            var httpClient = new HttpClient();
            
            // 创建 JsonSerializerOptions 以确保属性名称与服务器端匹配
            var options = new JsonSerializerOptions
            {
                PropertyNamingPolicy = null // 使用原始属性名称，不进行命名转换
            };
            
            // 记录请求内容
            var requestJson = JsonSerializer.Serialize(CurrentDeviceConfigure, options);
            Logger.LogInformation("发送配置请求: {}", requestJson);
            
            var r = await httpClient.PostAsync(new UriBuilder(BaseUrl)
            {
                Path = "configure"
            }.Uri, JsonContent.Create(CurrentDeviceConfigure, new MediaTypeHeaderValue("application/json")
            {
                CharSet = "utf-8"
            }, options));
            
            // 记录响应状态码和内容
            var responseContent = await r.Content.ReadAsStringAsync();
            Logger.LogInformation("响应状态码: {}, 响应内容: {}", r.StatusCode, responseContent);
            
            if (!r.IsSuccessStatusCode)
            {
                Logger.LogError("请求失败: {}", responseContent);
                throw new Exception($"请求失败: {r.StatusCode} - {responseContent}");
            }
            
            r.EnsureSuccessStatusCode();
        }
        catch (Exception e)
        {
            Logger.LogError(e, "无法保存配置");
            throw;
        }
    }
}