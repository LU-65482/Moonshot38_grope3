using RunSightConfigureClient.Services;

namespace RunSightConfigureClient;

public partial class MainPage : ContentPage
{
    public DeviceConnectionService DeviceConnectionService { get; } = App.GetService<DeviceConnectionService>();

    public MainPage()
    {
        BindingContext = this;
        InitializeComponent();
    }

    private void OnCounterClicked(object sender, EventArgs e)
    {
        
    }

    private void ButtonPairNew_OnClicked(object? sender, EventArgs e)
    {
        // Navigate to PairNewDevicePage
        Shell.Current.GoToAsync("//PairNew");
    }

    private async void ButtonSave_OnClicked(object? sender, EventArgs e)
    {
        try
        {
            await DeviceConnectionService.UploadSettings();
            await DisplayAlert("成功", "配置已保存", "确定");
        }
        catch (Exception exception)
        {
            await DisplayAlert("错误", $"保存配置时发生错误: {exception.Message}", "确定");
        }
    }
}