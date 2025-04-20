using CommunityToolkit.Mvvm.ComponentModel;

namespace RunSightConfigureClient.Models;

public partial class DeviceConfigure : ObservableObject
{
    [ObservableProperty] private double _speedThreshold = -5.5;
    [ObservableProperty] private string _wifiSSID = "";
    [ObservableProperty] private string _wifiPassword = "";
    [ObservableProperty] private int _uid = 0;
}