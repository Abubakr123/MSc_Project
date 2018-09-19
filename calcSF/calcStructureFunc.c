#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#define max_MCC 20000
#define max_DMs 2000
#define max_pairs 4000000

/* ############################################################################################### */
double calc_mean (double vals[], int count) {
  int ii;
  double sum = 0;
  for (ii=0;ii<count;ii++) {
    sum += vals[ii];
  }
  return sum / count;
}

/* ############################################################################################### */
double calc_sigma (double vals[], double mean, int count) {
  int ii;
  double delta;
  double sum_squares = 0;
  for (ii=0;ii<count;ii++) {
    delta = vals[ii] - mean;
    sum_squares += delta*delta;
  }
  return sqrt(sum_squares / count);
}

double random_double () {
  return (double) rand() / RAND_MAX;
}

/* ############################################################################################### */
void sort_data (double *MJD0, double *DM0, double *DMunc0, int size) {
  int ii,jj;
  int best_found;
  double dd;
  for(ii=0;ii<size;ii++) {
    best_found = -1;
    for (jj=ii;jj<size;jj++) {
      if (best_found == -1 || *(MJD0 + jj) < *(MJD0 + best_found)) {
	best_found = jj;
      }
    }
    dd = *(MJD0+ii);
    *(MJD0+ii) = *(MJD0+best_found);
    *(MJD0+best_found) = dd;
    dd = *(DM0+ii);
    *(DM0+ii) = *(DM0+best_found);
    *(DM0+best_found) = dd;
    dd = *(DMunc0+ii);
    *(DMunc0+ii) = *(DMunc0+best_found);
    *(DMunc0+best_found) = dd;
  }
}

/* ############################################################################################### */
// ref: http://www.design.caltech.edu/erik/Misc/Gaussian.html
double * random_gaussian () {
  double x1,x2,w;
  static double y[2];
  do {
    x1 = 2*random_double() - 1.0;
    x2 = 2*random_double() - 1.0;
    w = x1*x1 + x2*x2;
  } while (w >= 1);
  w = sqrt((-2.0*log(w))/w);
  y[0] = x1 * w;
  y[1] = x2 * w;
  return y;
}

/* ############################################################################################### */
double calcDDMforDMset(double tau, double tau_factor, double MJD[], double *DM_MC00, double DMunc[],
		       int measurement_count, int MC_it, int w, int *NP) {
  // constants for array size
  // int max_DeltaDMsq_vals_per_tau = measurement_count * measurement_count;
  // variables
  double DeltaDM;
  //double DeltaDMsq[max_DeltaDMsq_vals_per_tau];
  static double DeltaDMsq[max_pairs];
  //double weight[max_DeltaDMsq_vals_per_tau];
  static double weight[max_pairs];
  double weight_sum = 0;
  int ii,jj,cc = 0;

  double tau_range = sqrt(tau_factor);
  double min_diff = tau / tau_range;
  double max_diff = tau * tau_range;

  for (ii=0;ii<measurement_count;ii++) {
    jj = ii+1;
    for (jj=ii;jj<measurement_count;jj++) {
      if (MJD[ii] + min_diff < MJD[jj] && MJD[ii] + max_diff > MJD[jj]) {
	// DeltaDM = DM_MC[MC_it][jj] - DM_MC[MC_it][ii];
	// DeltaDM = (*(DM_MC00 + MC_it*measurement_count + jj)) - (*(DM_MC00 + MC_it*measurement_count + ii));
	DeltaDM = (*(DM_MC00 + MC_it*max_DMs + jj)) - (*(DM_MC00 + MC_it*max_DMs + ii));
	DeltaDMsq[cc] = DeltaDM*DeltaDM;

	// weighting, if wanted
	if (w) { weight[cc] = 1 / (DMunc[ii]*DMunc[ii] + DMunc[jj]*DMunc[jj]); } else { weight[cc] = 1; }
	weight_sum += weight[cc];

	cc++;
      }
    }
  }

  double sum = 0;
  for (ii=0;ii<cc;ii++) {
    sum += DeltaDMsq[ii] * weight[ii];
  }
  *NP = cc; // number of pairs used
  return sum / weight_sum;
}

/* ############################################################################################### */
void calcDDMforTAU(double tau, double tau_factor, double MJD[], double *DM_MC00, double DMunc[],
		   int measurement_count, int MCC, int w, double *outDDM, double *outDDMunc, int *outNP) {
  // vars
  double DDM[MCC];
  int it; // monte carlo iteration

  for (it=0;it<MCC;it++) {
    // calc DDM for this monte carlo iteration
    DDM[it] = calcDDMforDMset(tau,tau_factor,MJD,DM_MC00,DMunc,measurement_count,it,w,outNP);
  }

  // calculate mean and unc of DDM
  *outDDM = calc_mean(DDM,MCC);
  *outDDMunc = calc_sigma(DDM,*outDDM,MCC);
}

/* ############################################################################################### */
/* ############################################################################################### */
int main (int argc, char *argv[]) {
  // constants
  int max_line_length = 200;
  int measurement_count = 0;
  srand(234343);

  // variables for different purposes
  FILE *fp;
  int i,j;

  // settings
  int help = 0;
  int col_MJD = 1;
  int col_DM = 2;
  int col_DMunc = 5;
  char infile[200] = "Tempo2_DM_scripted.txt";
  char outfile[200] = "./scriptdata/structure_function.dat";
  double tau = 0.5;
  double tau_factor = 1.5;
  int weight = 0;
  int verbose = 0;
  int MCC = 1000; // monte carlo iteration count

  // input args
  for(i=1;i<argc;i++) {
    if (strcmp(argv[i-1],"-col_MJD") == 0) {
      if (!sscanf(argv[i],"%d",&col_MJD)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
    }
    else if (strcmp(argv[i-1],"-col_DM") == 0) {
      if (!sscanf(argv[i],"%d",&col_DM)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
    }
    else if (strcmp(argv[i-1],"-col_DMunc") == 0) {
      if (!sscanf(argv[i],"%d",&col_DMunc)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
    }
    else if (strcmp(argv[i-1],"-tau") == 0) {
      if (!sscanf(argv[i],"%lf",&tau)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
      else if (tau <= 0) {
	printf("Error: invalid argument for option '%s' (value=%.2lf, expected > 0)\n",argv[i-1],tau); help = 1; }
    }
    else if (strcmp(argv[i-1],"-tau_factor") == 0) {
      if (!sscanf(argv[i],"%lf",&tau_factor)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
      else if (tau_factor <= 1) {
	printf("Error: invalid argument for option '%s' (value=%.2lf, expected > 1)\n",argv[i-1],tau_factor); help = 1; }
    }
    else if (strcmp(argv[i-1],"-m") == 0) {
      if (!sscanf(argv[i],"%d",&MCC)) {
	printf("Error: expecting number as argument for option '%s'.\n",argv[i-1]); help = 1; }
      else if (MCC < 100 || MCC > 20000) {
	printf("Error: invalid argument for option '%s' (value=%d, expected between 100 and %d)\n",argv[i-1],MCC,max_MCC); help = 1; }
    }
    else if (strcmp(argv[i-1],"-infile") == 0 || strcmp(argv[i-1],"-i") == 0) { sscanf(argv[i],"%s",infile); }
    else if (strcmp(argv[i-1],"-outfile") == 0 || strcmp(argv[i-1],"-o") == 0) { sscanf(argv[i],"%s",outfile); }
    else if (strcmp(argv[i],"-w") == 0) { weight = 1; }
    else if (strcmp(argv[i],"-v") == 0) { verbose = 1; }
    else if (strcmp(argv[i],"-help") == 0 || strcmp(argv[i],"-h") == 0) { help = 1; }
    // check if valid arg that needs extra stuff
    // and print error if not
    else if (strcmp(argv[i],"-col_MJD") != 0 && strcmp(argv[i],"-col_DM") != 0 && strcmp(argv[i],"-col_DMunc") != 0 && 
	     strcmp(argv[i],"-tau") != 0 && strcmp(argv[i],"-tau_factor") != 0 && strcmp(argv[i],"-m") != 0 &&
	     strcmp(argv[i],"-infile") != 0 && strcmp(argv[i],"-i") != 0 && strcmp(argv[i],"-outfile") != 0 && strcmp(argv[i],"-o") != 0) { 
      printf("Error: Invalid argument '%s'.\n",argv[i]); help = 1; }
  }
  printf("\n");

  // help
  if (help) {
    printf("Written by Julian Donner.\n");
    printf("\n");
    printf("This program calculates the structure function\n");
    printf("D_DM(tau) = <[DM(t+tau)-DM(t)]^2>\n");
    printf("for a given set of DM values at different MJDs.\n");
    printf("For detailed information, read my MSc. thesis.\n");
    printf("The uncertainty is calculated through Monte Carlo simulation.\n\n");
    printf("Usage: calcStructureFunc [options]\n\n");
    printf("Available options:\n");
    printf("-help / -h\t\t print this help\n");
    printf("-infile / -i <file>\t set input file (current: %s)\n",infile);
    printf("-outfile / -o <file>\t set output file (current: %s)\n",outfile);
    printf("-col_MJD <num>\t\t set MJD column in input file (current: %d)\n",col_MJD);
    printf("-col_DM <num>\t\t set DM column in input file (current: %d)\n",col_DM);
    printf("-col_DMunc <num>\t set DMunc column in input file (current: %d)\n",col_DMunc);
    printf("-tau <num>\t\t set minimum probed time scale (current: %.2lf)\n",tau);
    printf("-tau_factor <num>\t set tau iteration factor (current: %.2lf)\n",tau_factor);
    printf("-m <num>\t\t set number of Monte Carlo iterations (current: %d)\n",MCC);
    printf("-w\t\t\t weight the [DM(t+tau)-DM(t)]^2 values by 1/[DMunc(t+tau)^2+DMunc(t)^2]\n");
    printf("-v\t\t\t verbose mode, e.g. prints dataset that was read in.\n");
    printf("\n");
    printf("Note:\tEvery line in the input file where the FIRST character is a '#' is ignored.\n");
    printf("Note:\tSingle points with large DM uncertainties can greatly increase the outcoming uncertainties.\n");
    printf("\tand corrupt the results.\n");
    printf("\tUse the '-w' option or remove those points in that case.\n");
    return 1;
  }

  // --------------------------------------------------------------------------------------------
  char lc[max_line_length];
  // count lines
  fp = fopen(infile,"r");
  if (fp == NULL) {
    printf("unable to read data file %s\n",infile);
    return 1;
  }
  while(fgets(lc,max_line_length,fp)) {
    if (lc[0] != '#') {
      measurement_count ++; }
  }
  fclose(fp);

  // readin
  double MJD[measurement_count],DM[measurement_count],DMunc[measurement_count];
  fp = fopen(infile, "r");
  int line = 0;
  int col;
  char *ptr; // to tokenise string
  while(fgets(lc,max_line_length,fp)) {
    if (lc[0] != '#') {
      col = 0;
      ptr = strtok(lc," ");
      while(ptr != NULL) {
	col ++;
	if (col == col_MJD) { sscanf(ptr,"%lf",&MJD[line]);}
	if (col == col_DM) { sscanf(ptr,"%lf",&DM[line]);}
	if (col == col_DMunc) { sscanf(ptr,"%lf",&DMunc[line]);}
	ptr = strtok(NULL," ");
      }
      line ++;
    }
  }
  fclose(fp);
  printf("read in %d measurements\n",measurement_count);

  // check if enough
  if (measurement_count < 5) {
    printf("Error: not enough data!\n");
    return 1;
  }

  // sort
  if (verbose) { printf("read-in data, sorted by MJD:\nMJD\t\tDM\t\tDMunc\n"); }
  sort_data(MJD,DM,DMunc,measurement_count);
  for(i=0;i<measurement_count;i++) {
    if (verbose) { printf("%lf\t%lf\t%e\n",MJD[i],DM[i],DMunc[i]); }
  }

  // monte carlo set
  // double DM_MC[MCC][measurement_count];
  static double DM_MC[max_MCC][max_DMs];
  int r = 1;
  double *randoms;
  for(i=0;i<MCC;i++) {
    for(j=0;j<measurement_count;j++) {
      if (r == 1) { randoms = random_gaussian(); r = 0; } else { r = 1; }
      DM_MC[i][j] = DM[j] + DMunc[j] * randoms[r];
    }
  }

  // calc structure func
  double length = MJD[measurement_count-1] - MJD[0];
  printf("total length of dataset: %lf\n",length);
  int max_taus = (int)(log(length/tau)/log(tau_factor)) + 2;

  double TAU[max_taus],DDM[max_taus],DDMunc[max_taus]; // final results
  int NP[max_taus]; // final results
  int tt = 0; // tau count
  while (tau < length) {
    // printf("tau = %.2lf\n",tau);

    // calculate DDM(tau) and write results to DDM[tt],DDMunc[tt],NP[tt]
    calcDDMforTAU(tau,tau_factor,MJD,&DM_MC[0][0],DMunc,measurement_count,MCC,weight,&DDM[tt],&DDMunc[tt],&NP[tt]);
    TAU[tt] = tau;
    
    // next tau
    tau *= tau_factor;
    tt++;
  }

  fp = fopen(outfile,"w");
  fprintf(fp,"# tau DDM DDMunc n_pairs\n");
  for(i=0;i<tt;i++) {
    fprintf(fp,"%.2lf %e %e %d\n",TAU[i],DDM[i],DDMunc[i],NP[i]);
  }
  fclose(fp);
  printf("Calculated D_DM(tau) for %d tau values\n",tt+1);

  return 0;
}
