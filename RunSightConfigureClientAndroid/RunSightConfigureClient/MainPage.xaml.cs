namespace RunSightConfigureClient;

public partial class MainPage : ContentPage
{
    int count = 0;

    public MainPage()
    {
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
}