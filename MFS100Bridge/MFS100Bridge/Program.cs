using System;
using System.Drawing;
using System.Drawing.Imaging;
using MANTRA;

class Program
{
    static void Main(string[] args)
    {
        try
        {
            string path;

            // 🔥 get filename from Python
            if (args.Length > 0)
                path = args[0];
            else
                path = "fingerprint.bmp";

            MFS100 device = new MFS100();

            int ret = device.Init();

            if (ret != 0)
            {
                Console.WriteLine("Device not connected");
                return;
            }

            Console.WriteLine("Place finger...");

            FingerData fingerData = new FingerData();

            ret = device.AutoCapture(ref fingerData, 10000, false, true);

            if (ret == 0)
            {
                Bitmap bmp = fingerData.FingerImage;

                bmp.Save(path, ImageFormat.Bmp);

                Console.WriteLine("Saved at: " + path);
            }
            else
            {
                Console.WriteLine("Capture failed");
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine("Error: " + ex.Message);
        }
    }
}