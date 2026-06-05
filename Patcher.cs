using System;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("======================================================");
        Console.WriteLine(" 레육계ds 한글패치 by hanbi.");
        Console.WriteLine("======================================================");
        Console.WriteLine("");
        
        Console.Write(" pin: ");
        string pin = Console.ReadLine();
        
        // Compute SHA256 of the PIN to get the AES Key
        byte[] key;
        using (SHA256 sha256 = SHA256.Create())
        {
            key = sha256.ComputeHash(Encoding.UTF8.GetBytes(pin));
        }
        
        Console.WriteLine("\n [!] patching...\n");
        
        string original = args.Length > 0 ? args[0] : "original.nds";
        string patch = "korean_patch_v6.dat";
        string output = "rei.nds";
        
        if (!File.Exists("xdelta3.exe"))
        {
            Console.WriteLine(" [error] xdelta3.exe missing");
            Console.WriteLine("\n press enter to exit");
            Console.ReadLine();
            return;
        }
        
        if (!File.Exists(original))
        {
            Console.WriteLine(string.Format(" [error] rom missing", original));
            Console.WriteLine(" \n fix:");
            Console.WriteLine(" 1. rename japanese rom to 'original.nds'");
            Console.WriteLine(" 2. or drag and drop rom to this exe");
            Console.WriteLine("\n press enter to exit");
            Console.ReadLine();
            return;
        }
        
        if (!File.Exists(patch))
        {
            Console.WriteLine(string.Format(" [error] patch missing ({0})", patch));
            Console.WriteLine("\n press enter to exit");
            Console.ReadLine();
            return;
        }
        
        Console.WriteLine(" decoding patch in memory......");
        
        byte[] patchData = File.ReadAllBytes(patch);
        if (patchData.Length < 16)
        {
            Console.WriteLine(" [error] corrupted dat file.");
            Console.ReadLine();
            return;
        }
        
        byte[] iv = new byte[16];
        Array.Copy(patchData, 0, iv, 0, 16);
        
        byte[] cipherText = new byte[patchData.Length - 16];
        Array.Copy(patchData, 16, cipherText, 0, cipherText.Length);
        
        byte[] decryptedPatch;
        try
        {
            using (AesCryptoServiceProvider aes = new AesCryptoServiceProvider())
            {
                aes.Key = key;
                aes.IV = iv;
                aes.Mode = CipherMode.CBC;
                aes.Padding = PaddingMode.PKCS7;
                
                using (ICryptoTransform decryptor = aes.CreateDecryptor(aes.Key, aes.IV))
                {
                    decryptedPatch = decryptor.TransformFinalBlock(cipherText, 0, cipherText.Length);
                }
            }
        }
        catch (CryptographicException)
        {
            Console.WriteLine("\n [!] pin invalid or file corrupted!");
            System.Threading.Thread.Sleep(3000);
            return;
        }
        
        Console.WriteLine(" patching......");
        
        ProcessStartInfo psi = new ProcessStartInfo();
        psi.FileName = "xdelta3.exe";
        psi.Arguments = string.Format("-d -c -s \"{0}\"", original);
        psi.UseShellExecute = false;
        psi.RedirectStandardInput = true;
        psi.RedirectStandardOutput = true;
        psi.CreateNoWindow = true;
        
        try
        {
            Process process = Process.Start(psi);
            
            // Asynchronously write to stdin
            Task writeTask = Task.Run(() =>
            {
                process.StandardInput.BaseStream.Write(decryptedPatch, 0, decryptedPatch.Length);
                process.StandardInput.Close();
            });
            
            // Read stdout to file
            using (FileStream fs = new FileStream(output, FileMode.Create, FileAccess.Write))
            {
                process.StandardOutput.BaseStream.CopyTo(fs);
            }
            
            writeTask.Wait();
            process.WaitForExit();
            
            if (process.ExitCode != 0)
            {
                Console.WriteLine("\n [error] patch failed! (wrong rom?)");
                Console.ReadLine();
                return;
            }
            
            Console.WriteLine("\n [done] patch success!");
            Console.WriteLine(string.Format(" output: {0}", output));
            Console.WriteLine("\n press enter to exit");
            Console.ReadLine();
        }
        catch (Exception ex)
        {
            Console.WriteLine("\n [error] runtime error: " + ex.Message);
            Console.ReadLine();
        }
    }
}
