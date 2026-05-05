using System;
using System.IO;
using MANTRA;
using SourceAFIS;
using System.Drawing.Imaging;

namespace FingerprintApp
{
    class Program
    {
        static MFS100 mfs100 = new MFS100();

        static byte[] CaptureTemplate()
        {
            var originalOut = Console.Out;
            Console.SetOut(Console.Error);

            FingerData fingerData = new FingerData();
            int ret = mfs100.AutoCapture(ref fingerData, 10000, true, false);

            Console.SetOut(originalOut);

            if (ret != 0)
                return null;

            using (MemoryStream ms = new MemoryStream())
            {
                fingerData.FingerImage.Save(ms, ImageFormat.Png);
                var image    = new FingerprintImage(ms.ToArray());
                var template = new FingerprintTemplate(image);
                return template.ToByteArray();
            }
        }
        static void Capture()
        {
            byte[] templateBytes = CaptureTemplate();

            if (templateBytes == null)
            {
                Console.WriteLine("ERROR:capture_failed");
                return;
            }

            Console.WriteLine("TEMPLATE:" + Convert.ToBase64String(templateBytes));
        }

        static void MatchPair(string liveB64, string storedB64)
        {
            try
            {
                byte[] liveBytes   = Convert.FromBase64String(liveB64);
                byte[] storedBytes = Convert.FromBase64String(storedB64);

                var liveTemplate   = new FingerprintTemplate(liveBytes);
                var storedTemplate = new FingerprintTemplate(storedBytes);

                double score = new FingerprintMatcher(storedTemplate).Match(liveTemplate);

                Console.WriteLine("SCORE:" + score.ToString("F4"));
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("match_pair error: " + ex.Message);
                Console.WriteLine("SCORE:-1");
            }
        }

        static void Main(string[] args)
        {
            var originalOut = Console.Out;
            Console.SetOut(Console.Error);
            int ret = mfs100.Init();
            Console.SetOut(originalOut);

            if (ret != 0)
            {
                Console.WriteLine("INIT_FAIL");
                return;
            }

            try
            {
                if (args.Length == 0)
                {
                    Console.WriteLine("INVALID_MODE");
                    return;
                }

                string mode = args[0].ToLower();

                if (mode == "capture")
                {
                    Capture();
                }
                else if (mode == "match_pair" && args.Length == 3)
                {
                    MatchPair(args[1], args[2]);
                }
                else
                {
                    Console.WriteLine("INVALID_MODE");
                }
            }
            finally
            {
                var o = Console.Out;
                Console.SetOut(Console.Error);
                mfs100.Dispose();
                Console.SetOut(o);
            }
        }
    }
}