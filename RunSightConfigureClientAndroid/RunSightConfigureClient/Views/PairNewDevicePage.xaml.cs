using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Microsoft.Maui.ApplicationModel;
using RunSightConfigureClient.Services;
using RunSightConfigureClient.ViewModels;

namespace RunSightConfigureClient.Views;

public partial class PairNewDevicePage : ContentPage
{
    public PairNewDeviceViewModel ViewModel { get; } = new();

    private DeviceConnectionService DeviceConnectionService { get; } = App.GetService<DeviceConnectionService>();

    public PairNewDevicePage()
    {
        BindingContext = this;
        InitializeComponent();
        RequestCameraPermission();
    }

    private async void RequestCameraPermission()
    {
        try
        {
            var status = await Permissions.CheckStatusAsync<Permissions.Camera>();
            
            if (status != PermissionStatus.Granted)
            {
                status = await Permissions.RequestAsync<Permissions.Camera>();
            }

            if (status != PermissionStatus.Granted)
            {
                await DisplayAlert("权限被拒绝", "需要摄像头权限才能继续", "确定");
            }
        }
        catch (Exception ex)
        {
            await DisplayAlert("错误", $"申请权限时发生错误: {ex.Message}", "确定");
        }
    }

    private async void ButtonConnect_OnClicked(object? sender, EventArgs e)
    {
        try
        {
            DeviceConnectionService.ConnectToNewDevice(ViewModel.ConnectionInfo);
            await DisplayAlert("成功", "成功连接到设备", "确定");
        }
        catch (Exception exception)
        {
            await DisplayAlert("错误", $"连接设备时发生错误: {exception.Message}", "确定");
        }
    }
}