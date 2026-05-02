using System;
using System.Drawing;
using System.Drawing.Imaging;
using Mantra.MFS100;

class Program
{
    static void Main()
    {
        try
        {
            MFS100 device = new MFS100();

            int ret = device.Init();

            if (ret != 0)
            {
                Console.WriteLine("INIT_FAILED");
                return;
            }

            Console.WriteLine("Place Finger...");

            byte[] imgData = new byte[256 * 360];

            int res = device.AutoCapture(imgData, 10000, false);

            if (res != 0)
            {
                Console.WriteLine("CAPTURE_FAILED");
                return;
            }

            Bitmap bmp = new Bitmap(256, 360);

            int i = 0;
            for (int y = 0; y < 360; y++)
            {
                for (int x = 0; x < 256; x++)
                {
                    int val = imgData[i++];
                    bmp.SetPixel(x, y, Color.FromArgb(val, val, val));
                }
            }

            bmp.Save("fingerprint.jpg", ImageFormat.Jpeg);

            Console.WriteLine("SUCCESS");
        }
        catch (Exception ex)
        {
            Console.WriteLine("ERROR");
        }
    }
}
